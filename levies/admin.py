from django.contrib import admin, messages
from django.utils.html import format_html
from auditlog.registry import auditlog

from .models import Levy, LevyTemplate, MemberLevy
from .services import apply_levy_template

# Register models with auditlog
auditlog.register(Levy)
auditlog.register(LevyTemplate)
auditlog.register(MemberLevy)


@admin.register(Levy)
class LevyAdmin(admin.ModelAdmin):
    list_display = ("name", "levy_type", "category", "amount", "is_active", "created_at")
    list_filter = ("levy_type", "category", "is_active")
    search_fields = ("name",)


# ── LevyTemplate Admin ────────────────────────────────────────

@admin.action(description="Apply selected template to all active members")
def apply_template_action(modeladmin, request, queryset):
    if queryset.count() != 1:
        modeladmin.message_user(
            request,
            "Please select exactly one template to apply.",
            messages.ERROR,
        )
        return
    template = queryset.first()
    if template.is_applied:
        modeladmin.message_user(
            request, "This template has already been applied.", messages.WARNING
        )
        return

    from django.utils import timezone
    period = timezone.now().date().replace(day=1)
    count = apply_levy_template(template, str(period), request.user)
    modeladmin.message_user(
        request,
        f"✔ Template '{template.name}' applied — {count} member levies created for {period}.",
        messages.SUCCESS,
    )


@admin.register(LevyTemplate)
class LevyTemplateAdmin(admin.ModelAdmin):
    list_display = (
        "name", "levy_type", "category", "amount",
        "applied_badge", "applied_at", "created_at",
    )
    list_filter = ("levy_type", "category", "is_applied")
    search_fields = ("name", "description")
    readonly_fields = ("is_applied", "applied_at", "applied_by", "created_at")
    actions = [apply_template_action]

    @admin.display(description="Status")
    def applied_badge(self, obj):
        from django.utils.html import mark_safe
        if obj.is_applied:
            return mark_safe(
                '<span style="background:#d1fae5;color:#065f46;padding:2px 10px;'
                'border-radius:12px;font-size:11px;font-weight:600;">&#10004; Applied</span>'
            )
        return mark_safe(
            '<span style="background:#fef3c7;color:#92400e;padding:2px 10px;'
            'border-radius:12px;font-size:11px;font-weight:600;">Draft</span>'
        )


@admin.register(MemberLevy)
class MemberLevyAdmin(admin.ModelAdmin):
    list_display = (
        "member", "levy", "period", "amount_due",
        "amount_paid_display", "balance_display", "status_badge",
    )
    list_filter = ("levy__levy_type", "period")
    search_fields = (
        "member__first_name", "member__last_name",
        "levy__name",
    )
    readonly_fields = ("amount_paid_display", "balance_display", "status_badge")

    @admin.display(description="Paid")
    def amount_paid_display(self, obj):
        return f"₦{obj.amount_paid:,.2f}"

    @admin.display(description="Balance")
    def balance_display(self, obj):
        return f"₦{obj.balance:,.2f}"

    @admin.display(description="Status")
    def status_badge(self, obj):
        from django.utils.html import mark_safe
        colours = {
            "PAID": ("d1fae5", "065f46", "&#10004; Paid"),
            "PARTIAL": ("fef3c7", "92400e", "Partial"),
            "UNPAID": ("fee2e2", "991b1b", "Unpaid"),
        }
        bg, fg, label = colours.get(obj.status, ("f3f4f6", "374151", obj.status))
        return mark_safe(
            f'<span style="background:#{bg};color:#{fg};padding:2px 10px;'
            f'border-radius:12px;font-size:11px;font-weight:600;">{label}</span>'
        )
