from django.contrib import admin, messages
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from auditlog.registry import auditlog

from .models import Member

auditlog.register(Member)


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = (
        "full_name", "phone", "email",
        "member_type", "status", "has_portal_access", "date_joined",
    )
    list_filter = ("status", "member_type")
    search_fields = ("first_name", "last_name", "phone", "house_address")
    readonly_fields = ("date_joined", "created_at", "updated_at")
    actions = ["create_portal_accounts", "send_debt_reminder_action"]

    @admin.display(description="Portal Access")
    def has_portal_access(self, obj):
        from django.utils.html import mark_safe
        if obj.user_id:
            return mark_safe(
                '<span style="color:#059669;font-weight:700;">&#10004; Active</span>'
            )
        return mark_safe('<span style="color:#9ca3af;">None</span>')

    @admin.action(description="Create portal login accounts for selected members")
    def create_portal_accounts(self, request, queryset):
        created = 0
        skipped = 0
        for member in queryset:
            if member.user_id:
                skipped += 1
                continue
            username = (
                f"{member.first_name.lower()}.{member.last_name.lower()}"
                .replace(" ", "")
            )
            # Make username unique
            base = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base}{counter}"
                counter += 1

            user = User.objects.create_user(
                username=username,
                password=member.phone,  # default password = phone number
                first_name=member.first_name,
                last_name=member.last_name,
                email=member.email or "",
            )
            member.user = user
            member.save(update_fields=["user"])
            created += 1

        self.message_user(
            request,
            f"✔ {created} portal account(s) created (default password = phone number). "
            f"{skipped} skipped (already had accounts).",
            messages.SUCCESS,
        )

    @admin.action(description="Send debt reminder to selected members")
    def send_debt_reminder_action(self, request, queryset):
        from notifications.tasks import send_monthly_debt_reminders
        ids = list(queryset.filter(status="ACTIVE").values_list("pk", flat=True))
        if not ids:
            self.message_user(request, "No active members selected.", messages.WARNING)
            return
        send_monthly_debt_reminders.delay()
        self.message_user(
            request,
            f"Debt reminders queued for {len(ids)} active member(s).",
            messages.SUCCESS,
        )


# ── Financial Secretary group bootstrap ───────────────────────

def _get_or_create_financial_secretary_group():
    """
    Call once from a migration or management command.
    Creates the 'Financial Secretary' group with safe permissions:
    - Can add payments, levies, member levies, levy templates, notifications
    - Cannot change or delete payments, allocations (audit protection)
    """
    group, _ = Group.objects.get_or_create(name="Financial Secretary")

    safe_add_models = [
        ("payments", "payment"),
        ("payments", "paymentallocation"),
        ("payments", "membercredit"),
        ("payments", "creditallocation"),
        ("levies", "levy"),
        ("levies", "memberlevy"),
        ("levies", "levytemplate"),
        ("notifications", "notification"),
    ]

    for app_label, model_name in safe_add_models:
        try:
            ct = ContentType.objects.get(app_label=app_label, model=model_name)
            add_perm = Permission.objects.get(content_type=ct, codename=f"add_{model_name}")
            view_perm = Permission.objects.get(content_type=ct, codename=f"view_{model_name}")
            group.permissions.add(add_perm, view_perm)
        except (ContentType.DoesNotExist, Permission.DoesNotExist):
            pass

    return group
