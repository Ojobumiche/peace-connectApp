from decimal import Decimal

from django import forms
from django.contrib import admin, messages
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html, mark_safe

from .models import (
    Payment,
    PaymentAllocation,
    MemberCredit,
    CreditAllocation,
)

from .services import CreditService, allocate_payment


# ============================================================
# PAYMENT ALLOCATION ACTION
# ============================================================

@admin.action(description="Allocate selected payments")
def allocate_selected_payments(
    modeladmin,
    request,
    queryset,
):
    success_count = 0

    for payment in queryset:
        allocate_payment(payment)
        success_count += 1

    modeladmin.message_user(
        request,
        f"{success_count} payment(s) allocated successfully.",
        messages.SUCCESS,
    )


# ============================================================
# PAYMENT ADMIN
# ============================================================

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):

    list_display = (
        "member",
        "amount",
        "payment_method",
        "reference",
        "payment_date",
        "allocation_status",
    )

    list_filter = (
        "payment_method",
        "payment_date",
    )

    search_fields = (
        "member__first_name",
        "member__last_name",
        "member__phone",
        "reference",
    )

    actions = (
        allocate_selected_payments,
    )

    def save_model(self, request, obj, form, change):
        """Auto-allocate immediately after every payment is saved."""
        super().save_model(request, obj, form, change)
        result = allocate_payment(obj)
        credit = result.get("credit", 0)
        allocated = result.get("allocated", 0)
        if allocated:
            self.message_user(
                request,
                f"Payment saved and ₦{allocated:,.2f} allocated to levies."
                + (f" ₦{credit:,.2f} added as member credit." if credit else ""),
                messages.SUCCESS,
            )

    @admin.display(description="Allocated")
    def allocation_status(self, obj):
        from decimal import Decimal
        from django.db.models import Sum
        total = (
            obj.allocations.aggregate(t=Sum("amount_allocated"))["t"]
            or Decimal("0.00")
        )
        if total >= obj.amount:
            return mark_safe(
                '<span style="color:#059669;font-weight:700;">&#10004; Full</span>'
            )
        if total > 0:
            return mark_safe(
                f'<span style="color:#d97706;font-weight:700;">Partial ₦{total:,.0f}</span>'
            )
        return mark_safe('<span style="color:#dc2626;font-weight:700;">None</span>')


# ============================================================
# PAYMENT ALLOCATION ADMIN
# ============================================================

@admin.register(PaymentAllocation)
class PaymentAllocationAdmin(admin.ModelAdmin):

    list_display = (
        "payment",
        "member",
        "member_levy",
        "amount_allocated",
        "created_at",
    )

    list_filter = (
        "created_at",
    )

    search_fields = (
        "payment__reference",
        "payment__member__first_name",
        "payment__member__last_name",
        "member_levy__member__first_name",
        "member_levy__member__last_name",
    )

    @admin.display(description="Member")
    def member(self, obj):
        return obj.payment.member


# ============================================================
# APPROVE CREDIT FORM
# ============================================================

class ApproveCreditForm(forms.Form):
    member_levy = forms.ModelChoiceField(
        queryset=None,
        label="Future Levy",
        help_text="Select the future levy to apply this credit toward.",
    )
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
        label="Amount to Apply",
    )
    approval_note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Approval Note",
        help_text="Optional note confirming the member's approval.",
    )

    def __init__(self, *args, member=None, **kwargs):
        super().__init__(*args, **kwargs)
        if member is not None:
            self.fields["member_levy"].queryset = (
                member.levies.filter(
                ).order_by("period")
            )


# ============================================================
# MEMBER CREDIT ADMIN
# ============================================================

@admin.register(MemberCredit)
class MemberCreditAdmin(admin.ModelAdmin):

    list_display = (
        "member",
        "payment",
        "amount",
        "amount_used_display",
        "credit_balance",
        "approval_badge",
        "approved_at",
        "created_at",
        "approve_action_button",
    )

    list_filter = (
        "approved_for_future_use",
        "created_at",
    )

    search_fields = (
        "member__first_name",
        "member__last_name",
        "member__phone",
        "payment__reference",
    )

    readonly_fields = (
        "amount_used_display",
        "credit_balance",
        "approval_badge",
        "created_at",
        "approved_at",
    )

    # ----------------------------------------------------------
    # Custom display columns
    # ----------------------------------------------------------

    @admin.display(description="Amount Used")
    def amount_used_display(self, obj):
        return f"₦{obj.amount_used_calculated:,.2f}"

    @admin.display(description="Balance")
    def credit_balance(self, obj):
        return f"₦{obj.balance:,.2f}"

    @admin.display(description="Status")
    def approval_badge(self, obj):
        if obj.approved_for_future_use:
            return mark_safe(
                '<span style="'
                "background:#d1fae5;color:#065f46;"
                "padding:2px 10px;border-radius:12px;"
                'font-size:11px;font-weight:600;">'
                "&#10004; Approved</span>"
            )
        return mark_safe(
            '<span style="'
            "background:#fee2e2;color:#991b1b;"
            "padding:2px 10px;border-radius:12px;"
            'font-size:11px;font-weight:600;">'
            "Pending</span>"
        )

    @admin.display(description="Action")
    def approve_action_button(self, obj):
        if obj.balance <= Decimal("0.00"):
            return format_html(
                '<span style="color:#9ca3af;font-size:12px;">No balance</span>'
            )
        url = reverse(
            "admin:payments_membercredit_approve_credit",
            args=[obj.pk],
        )
        return format_html(
            '<a href="{}" style="'
            "display:inline-block;padding:4px 12px;"
            "background:#2563eb;color:#fff;"
            "border-radius:6px;font-size:12px;"
            'text-decoration:none;font-weight:600;">'
            "Approve →</a>",
            url,
        )

    # ----------------------------------------------------------
    # Custom URL: two-step approve flow
    # ----------------------------------------------------------

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<path:object_id>/approve-credit/",
                self.admin_site.admin_view(self.approve_credit_view),
                name="payments_membercredit_approve_credit",
            ),
            path(
                "<path:object_id>/approve-credit/confirm/",
                self.admin_site.admin_view(self.confirm_credit_view),
                name="payments_membercredit_confirm_credit",
            ),
        ]
        return custom_urls + urls

    # ----------------------------------------------------------
    # Step 1 — enter levy + amount
    # ----------------------------------------------------------

    def approve_credit_view(self, request, object_id):
        credit = self.get_object(request, object_id)
        if credit is None:
            raise Http404

        if request.method == "POST":
            form = ApproveCreditForm(request.POST, member=credit.member)
            if form.is_valid():
                # Stash in session and move to confirmation step
                ml = form.cleaned_data["member_levy"]
                request.session["credit_approval"] = {
                    "credit_id": credit.pk,
                    "member_levy_id": ml.pk,
                    "amount": str(form.cleaned_data["amount"]),
                    "approval_note": form.cleaned_data["approval_note"],
                    # preview data for the confirmation page
                    "member_name": str(credit.member),
                    "levy_label": str(ml),
                    "levy_balance": str(ml.balance),
                    "credit_balance": str(credit.balance),
                }
                return HttpResponseRedirect(
                    reverse(
                        "admin:payments_membercredit_confirm_credit",
                        args=[credit.pk],
                    )
                )
        else:
            form = ApproveCreditForm(member=credit.member)

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "form": form,
            "credit": credit,
            "title": "Approve Credit for Future Levy",
            "original": credit,
            "step": 1,
        }
        return TemplateResponse(
            request,
            "admin/payments/membercredit/approve_credit.html",
            context,
        )

    # ----------------------------------------------------------
    # Step 2 — confirm before saving
    # ----------------------------------------------------------

    def confirm_credit_view(self, request, object_id):
        credit = self.get_object(request, object_id)
        if credit is None:
            raise Http404

        session_data = request.session.get("credit_approval")
        if (
            not session_data
            or session_data.get("credit_id") != credit.pk
        ):
            self.message_user(
                request,
                "Session expired. Please start the approval again.",
                messages.WARNING,
            )
            return HttpResponseRedirect(
                reverse(
                    "admin:payments_membercredit_approve_credit",
                    args=[credit.pk],
                )
            )

        if request.method == "POST":
            if "confirm" in request.POST:
                try:
                    from levies.models import MemberLevy
                    member_levy = MemberLevy.objects.get(
                        pk=session_data["member_levy_id"]
                    )
                    CreditService.approve_credit_for_levy(
                        credit=credit,
                        member_levy=member_levy,
                        amount=Decimal(session_data["amount"]),
                        approval_note=session_data["approval_note"],
                    )
                    del request.session["credit_approval"]
                    self.message_user(
                        request,
                        (
                            f"✔ ₦{session_data['amount']} credit approved "
                            f"for {session_data['levy_label']}."
                        ),
                        messages.SUCCESS,
                    )
                    return redirect(
                        "admin:payments_membercredit_changelist"
                    )
                except Exception as exc:
                    self.message_user(request, str(exc), messages.ERROR)

            # "Back" button — return to step 1
            return HttpResponseRedirect(
                reverse(
                    "admin:payments_membercredit_approve_credit",
                    args=[credit.pk],
                )
            )

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "credit": credit,
            "session_data": session_data,
            "title": "Confirm Credit Approval",
            "original": credit,
            "step": 2,
        }
        return TemplateResponse(
            request,
            "admin/payments/membercredit/confirm_credit.html",
            context,
        )

    @admin.action(description="Approve selected credit for a future levy")
    def approve_for_future_levy(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(
                request,
                "Please select exactly one credit item to approve.",
                messages.ERROR,
            )
            return

        credit = queryset.first()
        return HttpResponseRedirect(
            reverse(
                "admin:payments_membercredit_approve_credit",
                args=[credit.pk],
            )
        )

    actions = ("approve_for_future_levy",)


# ============================================================
# CREDIT ALLOCATION ADMIN
# ============================================================

@admin.register(CreditAllocation)
class CreditAllocationAdmin(admin.ModelAdmin):

    list_display = (
        "credit",
        "member",
        "member_levy",
        "amount_used_display",
        "approval_status",
        "approved_at_display",
        "created_at",
    )

    list_filter = (
        "credit__approved_for_future_use",
        "created_at",
    )

    search_fields = (
        "credit__member__first_name",
        "credit__member__last_name",
        "member_levy__member__first_name",
        "member_levy__member__last_name",
    )

    @admin.display(description="Member")
    def member(self, obj):
        return obj.credit.member

    @admin.display(description="Amount Applied")
    def amount_used_display(self, obj):
        return f"₦{obj.amount_allocated:,.2f}"

    @admin.display(description="Approved At")
    def approved_at_display(self, obj):
        return obj.credit.approved_at

    @admin.display(description="Approval")
    def approval_status(self, obj):
        if getattr(obj.credit, "approved_for_future_use", False):
            return mark_safe(
                '<span style="color:#065f46;font-weight:600;">&#10004; Approved</span>'
            )
        return mark_safe(
            '<span style="color:#991b1b;font-weight:600;">Pending</span>'
        )
