from rest_framework import serializers
from django.contrib.auth.models import User
from members.models import Member
from levies.models import Levy, LevyTemplate, MemberLevy
from payments.models import Payment, PaymentAllocation, MemberCredit, CreditAllocation
from notifications.models import Notification


# ── Auth ──────────────────────────────────────────────────────

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)


# ── Member ────────────────────────────────────────────────────

class MemberSummarySerializer(serializers.ModelSerializer):
    """Lightweight — used in lists and dashboard."""
    full_name = serializers.CharField(read_only=True)
    total_levy_due = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    total_levy_paid = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    outstanding_balance = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    available_credit = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    is_defaulter = serializers.BooleanField(read_only=True)

    class Meta:
        model = Member
        fields = [
            "id", "full_name", "first_name", "last_name",
            "phone", "email", "house_address", "member_type",
            "status", "date_joined",
            "total_levy_due", "total_levy_paid",
            "outstanding_balance", "available_credit", "is_defaulter",
        ]


class MemberProfileSerializer(serializers.ModelSerializer):
    """Full profile — used in member portal profile page."""
    full_name = serializers.CharField(read_only=True)
    outstanding_balance = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    available_credit = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = Member
        fields = [
            "id", "full_name", "first_name", "last_name",
            "phone", "whatsapp", "email", "house_address",
            "member_type", "status", "date_joined",
            "outstanding_balance", "available_credit",
        ]
        read_only_fields = [
            "id", "date_joined", "outstanding_balance", "available_credit",
        ]


# ── Levy ──────────────────────────────────────────────────────

class LevySerializer(serializers.ModelSerializer):
    class Meta:
        model = Levy
        fields = [
            "id", "name", "levy_type", "category",
            "amount", "description", "is_active", "created_at",
        ]


class LevyTemplateSerializer(serializers.ModelSerializer):
    applied_by_username = serializers.CharField(
        source="applied_by.username", read_only=True
    )

    class Meta:
        model = LevyTemplate
        fields = [
            "id", "name", "levy_type", "category", "amount",
            "description", "is_applied", "applied_at",
            "applied_by_username", "created_at",
        ]
        read_only_fields = ["is_applied", "applied_at", "applied_by_username"]


class MemberLevySerializer(serializers.ModelSerializer):
    levy_name = serializers.CharField(source="levy.name", read_only=True)
    levy_type = serializers.CharField(source="levy.levy_type", read_only=True)
    amount_paid = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    balance = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    status = serializers.CharField(read_only=True)
    member_name = serializers.CharField(source="member.full_name", read_only=True)

    class Meta:
        model = MemberLevy
        fields = [
            "id", "member", "member_name", "levy", "levy_name", "levy_type",
            "period", "amount_due", "amount_paid", "balance", "status", "created_at",
        ]
        read_only_fields = ["amount_paid", "balance", "status"]


# ── Payments ──────────────────────────────────────────────────

class PaymentSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.full_name", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id", "member", "member_name", "member_levy",
            "amount", "payment_method", "reference",
            "payment_date", "notes", "created_at",
        ]
        read_only_fields = ["created_at"]


class PaymentAllocationSerializer(serializers.ModelSerializer):
    levy_name = serializers.CharField(
        source="member_levy.levy.name", read_only=True
    )

    class Meta:
        model = PaymentAllocation
        fields = [
            "id", "payment", "member_levy", "levy_name",
            "amount_allocated", "created_at",
        ]


# ── Credits ──────────────────────────────────────────────────

class MemberCreditSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.full_name", read_only=True)
    payment_reference = serializers.CharField(
        source="payment.reference", read_only=True
    )
    amount_used_calculated = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    balance = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = MemberCredit
        fields = [
            "id", "member", "member_name", "payment", "payment_reference",
            "amount", "amount_used_calculated", "balance",
            "approved_for_future_use", "approved_at", "approval_note",
            "created_at",
        ]


class CreditAllocationSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(
        source="credit.member.full_name", read_only=True
    )
    levy_name = serializers.CharField(
        source="member_levy.levy.name", read_only=True
    )

    class Meta:
        model = CreditAllocation
        fields = [
            "id", "credit", "member_name", "member_levy",
            "levy_name", "amount_allocated", "created_at",
        ]


# ── Notifications ─────────────────────────────────────────────

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id", "notification_type", "channel", "status",
            "title", "body", "is_read", "sent_at", "read_at", "created_at",
        ]
        read_only_fields = [
            "notification_type", "channel", "status",
            "title", "body", "sent_at", "read_at", "created_at",
        ]


# ── Analytics ─────────────────────────────────────────────────

class TopContributorSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    full_name = serializers.CharField()
    total_paid = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_due = serializers.DecimalField(max_digits=12, decimal_places=2)


class DefaulterSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    full_name = serializers.CharField()
    phone = serializers.CharField()
    outstanding_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
