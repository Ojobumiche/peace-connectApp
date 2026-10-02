from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from .models import (
    Payment,
    PaymentAllocation,
    MemberCredit,
    CreditAllocation,
)

from levies.models import MemberLevy


ZERO = Decimal("0.00")



class CreditService:
    @staticmethod
    def get_available_credit(member):
        """
        Return the member's total unused credit.
        """
        total_credits = (
            MemberCredit.objects.filter(member=member)
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

        total_used = (
            CreditAllocation.objects
            .filter(credit__member=member)
            .aggregate(total=Sum("amount_allocated"))["total"]
            or Decimal("0.00")
        )
        return total_credits - total_used

    @staticmethod
    @transaction.atomic
    def create_credit(payment, amount):
        """
        Create credit for an excess payment.

        A zero or negative amount creates nothing.
        """
        if amount <= ZERO:
            return None

        existing_credit = (
            MemberCredit.objects
            .filter(payment=payment)
            .first()
        )

        if existing_credit:
            return existing_credit

        return MemberCredit.objects.create(
            member=payment.member,
            payment=payment,
            amount=amount,
        )

    @staticmethod
    @transaction.atomic
    def approve_credit_for_levy(
        credit,
        member_levy,
        amount,
        approval_note="",
    ):
        """
        Explicitly approve a selected MemberCredit against a specific
        future MemberLevy for the specified amount.
        """
        if amount <= ZERO:
            raise ValueError(
                "Credit allocation amount must be greater than zero."
            )

        if member_levy.member_id != credit.member_id:
            raise ValueError(
                "This levy does not belong to the selected member."
            )

        available_credit = credit.balance
        if available_credit <= ZERO:
            raise ValueError(
                "This member has no available credit."
            )

        payment_paid = (
            PaymentAllocation.objects
            .filter(member_levy=member_levy)
            .aggregate(total=Sum("amount_allocated"))["total"]
            or ZERO
        )

        credit_paid = (
            CreditAllocation.objects
            .filter(member_levy=member_levy)
            .aggregate(total=Sum("amount_allocated"))["total"]
            or ZERO
        )

        levy_balance = (
            member_levy.amount_due
            - payment_paid
            - credit_paid
        )

        if levy_balance <= ZERO:
            raise ValueError(
                "This levy has already been fully paid."
            )

        allocation_amount = min(
            amount,
            available_credit,
            levy_balance,
        )

        if allocation_amount <= ZERO:
            raise ValueError(
                "Credit allocation amount must be greater than zero."
            )

        credit.approved_for_future_use = True
        credit.approved_at = timezone.now()
        credit.approval_note = approval_note
        credit.save(update_fields=[
            "approved_for_future_use",
            "approved_at",
            "approval_note",
        ])

        allocation = CreditAllocation.objects.create(
            credit=credit,
            member_levy=member_levy,
            amount_allocated=allocation_amount,
        )

        return allocation

    @staticmethod
    @transaction.atomic
    def apply_credit_to_future_levy(
        member,
        member_levy,
        amount,
        approval_note="",
    ):
        """
        Backward-compatible wrapper for approving an available credit
        against a specific future levy.
        """
        credit = (
            MemberCredit.objects
            .select_for_update()
            .filter(member=member)
            .order_by("created_at")
            .first()
        )

        if not credit:
            raise ValueError("This member has no credit.")

        return CreditService.approve_credit_for_levy(
            credit,
            member_levy,
            amount,
            approval_note,
        )


@transaction.atomic
def allocate_payment(payment):
    """
    Allocate a payment against the member's outstanding levies.

    Any amount remaining after all eligible levies are satisfied
    becomes member credit.
    """

    remaining = payment.amount

    already_allocated = (
        PaymentAllocation.objects
        .filter(payment=payment)
        .aggregate(total=Sum("amount_allocated"))["total"]
        or ZERO
    )

    remaining -= already_allocated

    if remaining <= ZERO:
        return {
            "payment": payment,
            "allocated": already_allocated,
            "credit": ZERO,
        }

    total_allocated = already_allocated
    levies = (
        MemberLevy.objects
        .filter(member=payment.member)
        .order_by("period", "id")
    )

    for levy in levies:
        if remaining <= ZERO:
            break

        payment_paid = (
            PaymentAllocation.objects
            .filter(member_levy=levy)
            .aggregate(total=Sum("amount_allocated"))["total"]
            or ZERO
        )

        credit_paid = (
            CreditAllocation.objects
            .filter(member_levy=levy)
            .aggregate(total=Sum("amount_allocated"))["total"]
            or ZERO
        )

        total_paid = payment_paid + credit_paid
        balance = levy.amount_due - total_paid

        if balance <= ZERO:
            continue

        allocation_amount = min(remaining, balance)

        PaymentAllocation.objects.create(
            payment=payment,
            member_levy=levy,
            amount_allocated=allocation_amount,
        )

        remaining -= allocation_amount
        total_allocated += allocation_amount

    credit_amount = remaining

    if credit_amount > ZERO:
        CreditService.create_credit(
            payment=payment,
            amount=credit_amount,
        )

    return {
        "payment": payment,
        "allocated": total_allocated,
        "credit": credit_amount,
    }
