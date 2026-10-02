from datetime import date, datetime
from decimal import Decimal

from django.test import TestCase

from levies.models import Levy, LevyType, MemberLevy
from members.models import Member
from payments.models import (
    CreditAllocation,
    MemberCredit,
    Payment,
    PaymentMethod,
)
from payments.services import CreditService


class CreditApprovalFlowTests(TestCase):
    def setUp(self):
        self.member = Member.objects.create(
            first_name="Jane",
            last_name="Doe",
            phone="08011111111",
            house_address="12 Peace Road",
        )
        self.payment = Payment.objects.create(
            member=self.member,
            amount=Decimal("600.00"),
            payment_method=PaymentMethod.CASH,
            reference="PAY-APPROVAL-001",
            payment_date=datetime(2026, 8, 1, 9, 0, 0),
        )
        self.credit = MemberCredit.objects.create(
            member=self.member,
            payment=self.payment,
            amount=Decimal("600.00"),
        )
        self.future_levy = MemberLevy.objects.create(
            member=self.member,
            levy=Levy.objects.create(
                name="October Special Levy",
                levy_type=LevyType.SECURITY,
                amount=Decimal("3000.00"),
            ),
            period=date(2026, 10, 1),
            amount_due=Decimal("3000.00"),
        )

    def test_approve_credit_for_future_levy_explicit_amount(self):
        allocation = CreditService.approve_credit_for_levy(
            self.credit,
            self.future_levy,
            Decimal("250.00"),
            "Approved for October levy",
        )

        self.credit.refresh_from_db()
        self.assertTrue(self.credit.approved_for_future_use)
        self.assertEqual(self.credit.approval_note, "Approved for October levy")
        self.assertIsNotNone(self.credit.approved_at)
        self.assertEqual(allocation.amount_allocated, Decimal("250.00"))
        self.assertTrue(
            CreditAllocation.objects.filter(
                credit=self.credit,
                member_levy=self.future_levy,
                amount_allocated=Decimal("250.00"),
            ).exists()
        )

    def test_approve_credit_for_future_levy_rejects_excess_amount(self):
        with self.assertRaisesMessage(ValueError, "Credit allocation amount must be greater than zero."):
            CreditService.approve_credit_for_levy(
                self.credit,
                self.future_levy,
                Decimal("0.00"),
            )

        with self.assertRaisesMessage(ValueError, "This levy does not belong to the selected member."):
            other_member = Member.objects.create(
                first_name="John",
                last_name="Smith",
                phone="08022222222",
                house_address="99 New Street",
            )
            other_levy = MemberLevy.objects.create(
                member=other_member,
                levy=Levy.objects.create(
                    name="Other Levy",
                    levy_type=LevyType.MONTHLY,
                    amount=Decimal("4000.00"),
                ),
                period=date(2026, 11, 1),
                amount_due=Decimal("4000.00"),
            )
            CreditService.approve_credit_for_levy(
                self.credit,
                other_levy,
                Decimal("100.00"),
            )

        with self.assertRaisesMessage(ValueError, "This levy has already been fully paid."):
            self.future_levy.amount_due = Decimal("250.00")
            self.future_levy.save(update_fields=["amount_due"])
            CreditAllocation.objects.create(
                credit=self.credit,
                member_levy=self.future_levy,
                amount_allocated=Decimal("250.00"),
            )
            CreditService.approve_credit_for_levy(
                self.credit,
                self.future_levy,
                Decimal("50.00"),
            )
