from django.contrib.auth.models import User
from django.db import models
from decimal import Decimal
from django.db.models import Sum


class Member(models.Model):

    class MemberType(models.TextChoices):
        LAND_LORD = "LAND_LORD", "Land Lord"
        TENANT = "TENANT", "Tenant"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    # ── Link to Django auth user (member portal login) ──
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="member_profile",
        help_text="Django user account for member portal login.",
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, unique=True)
    whatsapp = models.CharField(
        max_length=20,
        blank=True,
        help_text="WhatsApp number (if different from phone).",
    )
    email = models.EmailField(blank=True, null=True)
    house_address = models.CharField(max_length=255)

    member_type = models.CharField(
        max_length=20,
        choices=MemberType.choices,
        default=MemberType.TENANT,
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    date_joined = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    # ── Financial summary properties ──────────────────────────

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def total_levy_due(self):
        return (
            self.levies.aggregate(total=Sum("amount_due"))["total"]
            or Decimal("0.00")
        )

    @property
    def total_levy_paid(self):
        from payments.models import PaymentAllocation, CreditAllocation
        payment_total = (
            PaymentAllocation.objects
            .filter(member_levy__member=self)
            .aggregate(total=Sum("amount_allocated"))["total"]
            or Decimal("0.00")
        )
        credit_total = (
            CreditAllocation.objects
            .filter(member_levy__member=self)
            .aggregate(total=Sum("amount_allocated"))["total"]
            or Decimal("0.00")
        )
        return payment_total + credit_total

    @property
    def outstanding_balance(self):
        return max(self.total_levy_due - self.total_levy_paid, Decimal("0.00"))

    @property
    def available_credit(self):
        from payments.models import MemberCredit, CreditAllocation
        total_credit = (
            MemberCredit.objects.filter(member=self)
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )
        total_used = (
            CreditAllocation.objects
            .filter(credit__member=self)
            .aggregate(total=Sum("amount_allocated"))["total"]
            or Decimal("0.00")
        )
        return max(total_credit - total_used, Decimal("0.00"))

    @property
    def is_defaulter(self):
        return self.outstanding_balance > Decimal("0.00")
