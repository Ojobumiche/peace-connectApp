from django.db import models, transaction
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum

ZERO = Decimal("0.00")


"""Payments model"""
class PaymentMethod(models.TextChoices):
    CASH = "CASH", "Cash"
    BANK_TRANSFER = "BANK_TRANSFER", "Bank Transfer"
    POS = "POS", "POS"
    ONLINE = "ONLINE", "Online Payment"


class Payment(models.Model):
    member = models.ForeignKey(
        "members.Member",
        on_delete=models.PROTECT,
        related_name="payments",
    )

    member_levy = models.ForeignKey(
        "levies.MemberLevy",
        on_delete=models.PROTECT,
        related_name="payments",
        blank=True,
        null=True,
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
    )

    reference = models.CharField(
        max_length=100,
        unique=True,
    )

    payment_date = models.DateTimeField()

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-payment_date"]

    def __str__(self):
        return (
            f"{self.member} - "
            f"₦{self.amount} - "
            f"{self.reference}"
        )
class PaymentAllocation(models.Model):
    payment = models.ForeignKey(
        Payment,
        on_delete=models.PROTECT,
        related_name="allocations",
        null=True,
    )
    member_levy = models.ForeignKey(
        "levies.MemberLevy",
        on_delete=models.PROTECT,
        related_name="allocations",
    )
    amount_allocated = models.DecimalField(
        
        max_digits=12,
        decimal_places=2,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["-created_at"]
    
    def __str__(self):
        return (
            f"Payment: {self.payment.reference} - "
            f"Member Levy: {self.member_levy.levy} - "
            f"Amount Allocated: ₦{self.amount_allocated}"
        )
    def clean(self):
        if not self.payment_id or not self.member_levy_id:
            return

    # Make sure the payment and levy belong to the same member
        if self.payment.member_id != self.member_levy.member_id:
            raise ValidationError(
            "The payment and Member Levy must belong to the same member."
        )

    # Total already allocated from this payment
        existing_payment_allocations = (
        PaymentAllocation.objects
        .filter(payment=self.payment)
        .exclude(pk=self.pk)
        .aggregate(
            total=models.Sum("amount_allocated")
        )["total"]
        or Decimal("0.00")
    )

        payment_remaining = (
        self.payment.amount - existing_payment_allocations
    )

        if self.amount_allocated > payment_remaining:
            raise ValidationError(
            f"This payment only has ₦{payment_remaining} "
            f"available for allocation."
        )

    # Total already allocated to this MemberLevy
        existing_levy_allocations = (
        PaymentAllocation.objects
        .filter(member_levy=self.member_levy)
        .exclude(pk=self.pk)
        .aggregate(
            total=models.Sum("amount_allocated")
        )["total"]
        or Decimal("0.00")
    )

        levy_remaining = (
        self.member_levy.amount_due - existing_levy_allocations
    )

        if self.amount_allocated > levy_remaining:
            raise ValidationError(
            f"This levy only has ₦{levy_remaining} "
            f"remaining."
        )

        if self.amount_allocated <= 0:
            raise ValidationError(
            "Allocated amount must be greater than zero."
        )
            
            
            
class MemberCredit(models.Model):
    member = models.ForeignKey(
        "members.Member",
        on_delete=models.PROTECT,
        related_name="credits",
    )

    payment = models.ForeignKey(
        Payment,
        on_delete=models.PROTECT,
        related_name="credits",
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    amount_used = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )
    
    approved_for_future_use = models.BooleanField(
        default=False,
        help_text=("Member has approved this credit"
        " for future levy allocation."
    ),
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    approval_note = models.TextField(
        blank=True,
    )
    approved_note = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )
    

    class Meta:
        ordering = ["-created_at"]
    
    def __str__(self):
        return (
            f"{self.credit.member} - "
            f"{self.member_levy} - "
            f"₦{self.amount_allocated:,.2f}"
        )

    @property
    def amount_used_calculated(self):
        total_allocated = (
            self.allocations.aggregate(
                total=models.Sum("amount_allocated")
            )["total"]
            or Decimal("0.00")
        )

        return total_allocated

    @property
    def balance(self):
        balance = (
            self.amount -
            self.amount_used_calculated
        )

        return max(balance, Decimal("0.00"))

    def __str__(self):
        return (
            f"{self.member} - "
            f"Credit ₦{self.balance:,.2f}"
        )


class CreditAllocation(models.Model):
    credit = models.ForeignKey(
        MemberCredit,
        on_delete=models.PROTECT,
        related_name="allocations",
    )

    member_levy = models.ForeignKey(
        "levies.MemberLevy",
        on_delete=models.PROTECT,
        related_name="credit_allocations",
    )

    amount_allocated = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return (
            f"{self.credit.member} - "
            f"{self.member_levy} - "
            f"₦{self.amount_allocated}"
        )
        
class CreditService:

    @staticmethod
    def get_available_credit(member):
        ...
    
    @staticmethod
    def create_credit(payment, amount):
        ...

    @staticmethod
    @transaction.atomic
    def apply_credit(
        member,
        member_levy,
        amount,
    ):
        """
        Apply a member's credit to a specific levy.

        Future levy allocation is only allowed when the
        member has explicitly approved the credit for
        future use.
        """

        if amount <= ZERO:
            raise ValueError(
                "Credit allocation amount must be greater than zero."
            )

        credit = (
            MemberCredit.objects
            .select_for_update()
            .filter(
                member=member,
                approved_for_future_use = False,
            )
            .order_by("created_at")
            .first()
        )

        if not credit:
            raise ValueError(
                "No approved member credit is available."
            )

        if credit.balance <= ZERO:
            raise ValueError(
                "The member has no available credit."
            )

        # Make sure the levy belongs to the same member.
        if member_levy.member_id != member.id:
            raise ValueError(
                "This levy does not belong to the selected member."
            )

        # --------------------------------------------------
        # Calculate levy balance
        # --------------------------------------------------

        payment_paid = (
            PaymentAllocation.objects
            .filter(member_levy=member_levy)
            .aggregate(
                total=Sum("amount_allocated")
            )["total"]
            or ZERO
        )

        credit_paid = (
            CreditAllocation.objects
            .filter(member_levy=member_levy)
            .aggregate(
                total=Sum("amount_allocated")
            )["total"]
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

        # --------------------------------------------------
        # Determine maximum allocation
        # --------------------------------------------------

        allocation_amount = min(
            amount,
            credit.balance,
            levy_balance,
        )

        if allocation_amount <= ZERO:
            raise ValueError(
                "No amount is available for allocation."
            )

        # --------------------------------------------------
        # Create credit allocation
        # --------------------------------------------------

        allocation = CreditAllocation.objects.create(
            credit=credit,
            member_levy=member_levy,
            amount_allocated=allocation_amount,
        )

        return allocation