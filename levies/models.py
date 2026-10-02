from decimal import Decimal
from django.db import models
from django.db.models import Sum


class LevyCategory(models.TextChoices):
    RECURRING = "RECURRING", "Recurring"
    ONE_TIME = "ONE_TIME", "One-Time"
    PROJECT = "PROJECT", "Community Project"


class LevyType(models.TextChoices):
    MONTHLY = "MONTHLY", "Monthly Contribution"
    SECURITY = "SECURITY", "Security Levy"
    SOLAR = "SOLAR", "Solar Light Project"
    POL_LIGHT = "POL_LIGHT", "Pol Light Connection"
    REHABILITATION = "REHABILITATION", "Community Rehabilitation"
    PARTY = "PARTY", "Get-together/Party Levy"
    PROJECT = "PROJECT", "Community Project"
    OTHER = "OTHER", "Other"


class Levy(models.Model):
    name = models.CharField(max_length=100)

    levy_type = models.CharField(
        max_length=20,
        choices=LevyType.choices,
    )

    category = models.CharField(
        max_length=20,
        choices=LevyCategory.choices,
        default=LevyCategory.RECURRING,
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Levies"

    def __str__(self):
        return f"{self.name} — ₦{self.amount:,.0f}"


class LevyTemplate(models.Model):
    """
    Reusable template for any future community project levy.
    The secretary creates one, fills in name/type/amount/description,
    then uses the admin action to bulk-assign it to all active members.
    """
    name = models.CharField(max_length=150)
    levy_type = models.CharField(
        max_length=20,
        choices=LevyType.choices,
        default=LevyType.PROJECT,
    )
    category = models.CharField(
        max_length=20,
        choices=LevyCategory.choices,
        default=LevyCategory.PROJECT,
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)

    # track when it was applied
    applied_at = models.DateTimeField(null=True, blank=True)
    applied_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="applied_levy_templates",
    )
    is_applied = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        status = "✔ Applied" if self.is_applied else "Draft"
        return f"{self.name} — ₦{self.amount:,.0f} [{status}]"


class MemberLevy(models.Model):
    member = models.ForeignKey(
        "members.Member",
        on_delete=models.CASCADE,
        related_name="levies",
    )
    levy = models.ForeignKey(
        Levy,
        on_delete=models.PROTECT,
        related_name="member_levies",
    )
    period = models.DateField(
        help_text="The month/period this levy applies to."
    )
    amount_due = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-period"]
        constraints = [
            models.UniqueConstraint(
                fields=["member", "levy", "period"],
                name="unique_member_levy_period",
            )
        ]

    def __str__(self):
        return f"{self.member} — {self.levy.name} — {self.period}"

    @property
    def amount_paid(self):
        from payments.models import PaymentAllocation, CreditAllocation
        payment_total = (
            self.allocations.aggregate(total=Sum("amount_allocated"))["total"]
            or Decimal("0.00")
        )
        credit_total = (
            self.credit_allocations.aggregate(total=Sum("amount_allocated"))["total"]
            or Decimal("0.00")
        )
        return payment_total + credit_total

    @property
    def balance(self):
        return max(self.amount_due - self.amount_paid, Decimal("0.00"))

    @property
    def status(self):
        if self.amount_paid <= Decimal("0.00"):
            return "UNPAID"
        if self.balance <= Decimal("0.00"):
            return "PAID"
        return "PARTIAL"
