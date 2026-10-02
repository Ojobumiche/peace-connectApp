from decimal import Decimal

from django.contrib.auth import authenticate
from django.db.models import Sum
from django.utils import timezone
from rest_framework import generics, status, views
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from members.models import Member
from levies.models import Levy, LevyTemplate, MemberLevy
from payments.models import Payment, MemberCredit, CreditAllocation, PaymentAllocation
from notifications.models import Notification, NotificationStatus

from .permissions import IsFinancialSecretary, IsOwnerMember, IsMemberOrStaff
from .serializers import (
    MemberSummarySerializer, MemberProfileSerializer,
    LevySerializer, LevyTemplateSerializer, MemberLevySerializer,
    PaymentSerializer, MemberCreditSerializer,
    NotificationSerializer,
    TopContributorSerializer, DefaulterSerializer,
    ChangePasswordSerializer,
)


# ── Auth ──────────────────────────────────────────────────────

class LoginView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username", "").strip()
        password = request.data.get("password", "")
        user = authenticate(request, username=username, password=password)
        if not user:
            return Response(
                {"detail": "Invalid username or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        refresh = RefreshToken.for_user(user)
        member = getattr(user, "member_profile", None)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.pk,
                "username": user.username,
                "is_staff": user.is_staff,
                "member_id": member.pk if member else None,
                "full_name": member.full_name if member else user.get_full_name(),
            },
        })


class LogoutView(views.APIView):
    def post(self, request):
        try:
            token = RefreshToken(request.data["refresh"])
            token.blacklist()
        except Exception:
            pass
        return Response({"detail": "Logged out."})


class ChangePasswordView(views.APIView):
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data["old_password"]):
            return Response(
                {"old_password": "Incorrect password."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.set_password(serializer.validated_data["new_password"])
        user.save()
        return Response({"detail": "Password changed."})


# ── Member Portal — own data only ────────────────────────────

class MemberDashboardView(views.APIView):
    """
    Returns the logged-in member's full financial summary.
    Staff can pass ?member_id= to view any member.
    """
    def get(self, request):
        if request.user.is_staff and request.query_params.get("member_id"):
            member = Member.objects.get(pk=request.query_params["member_id"])
        else:
            member = getattr(request.user, "member_profile", None)
            if not member:
                return Response(
                    {"detail": "No member profile linked to this account."},
                    status=404,
                )

        # Levy breakdown
        levies = member.levies.select_related("levy").order_by("-period")[:5]
        levy_data = MemberLevySerializer(levies, many=True).data

        # Recent payments
        payments = Payment.objects.filter(member=member).order_by("-payment_date")[:5]
        payment_data = PaymentSerializer(payments, many=True).data

        return Response({
            "member": MemberProfileSerializer(member).data,
            "recent_levies": levy_data,
            "recent_payments": payment_data,
            "unread_notifications": member.notifications.filter(is_read=False).count(),
        })


class MyLeviesView(generics.ListAPIView):
    serializer_class = MemberLevySerializer

    def get_queryset(self):
        if self.request.user.is_staff and self.request.query_params.get("member_id"):
            return MemberLevy.objects.filter(
                member_id=self.request.query_params["member_id"]
            ).select_related("levy", "member")
        member = getattr(self.request.user, "member_profile", None)
        if not member:
            return MemberLevy.objects.none()
        return member.levies.select_related("levy").order_by("-period")


class MyPaymentsView(generics.ListAPIView):
    serializer_class = PaymentSerializer

    def get_queryset(self):
        if self.request.user.is_staff and self.request.query_params.get("member_id"):
            return Payment.objects.filter(
                member_id=self.request.query_params["member_id"]
            )
        member = getattr(self.request.user, "member_profile", None)
        if not member:
            return Payment.objects.none()
        return Payment.objects.filter(member=member).order_by("-payment_date")


class MyCreditView(generics.ListAPIView):
    serializer_class = MemberCreditSerializer

    def get_queryset(self):
        member = getattr(self.request.user, "member_profile", None)
        if self.request.user.is_staff and self.request.query_params.get("member_id"):
            return MemberCredit.objects.filter(
                member_id=self.request.query_params["member_id"]
            )
        if not member:
            return MemberCredit.objects.none()
        return MemberCredit.objects.filter(member=member)


class MyProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = MemberProfileSerializer

    def get_object(self):
        return getattr(self.request.user, "member_profile", None)


class MyNotificationsView(generics.ListAPIView):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        member = getattr(self.request.user, "member_profile", None)
        if not member:
            return Notification.objects.none()
        return member.notifications.filter(
            channel__in=["IN_APP", "EMAIL"]
        ).order_by("-created_at")


class MarkNotificationReadView(views.APIView):
    def post(self, request, pk):
        member = getattr(request.user, "member_profile", None)
        try:
            n = Notification.objects.get(pk=pk, member=member)
            n.is_read = True
            n.read_at = timezone.now()
            n.save(update_fields=["is_read", "read_at"])
            return Response({"detail": "Marked as read."})
        except Notification.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)


# ── Staff / Secretary views ───────────────────────────────────

class MemberListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsFinancialSecretary]
    serializer_class = MemberSummarySerializer
    queryset = Member.objects.filter(status="ACTIVE").order_by("last_name")


class LevyListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsFinancialSecretary]
    serializer_class = LevySerializer
    queryset = Levy.objects.all()


class LevyTemplateListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsFinancialSecretary]
    serializer_class = LevyTemplateSerializer
    queryset = LevyTemplate.objects.all()


class LevyTemplateApplyView(views.APIView):
    """
    POST /api/levy-templates/<pk>/apply/
    Bulk-creates MemberLevy for every active member using the template.
    """
    permission_classes = [IsAuthenticated, IsFinancialSecretary]

    def post(self, request, pk):
        from levies.services import apply_levy_template
        try:
            template = LevyTemplate.objects.get(pk=pk)
        except LevyTemplate.DoesNotExist:
            return Response({"detail": "Template not found."}, status=404)

        if template.is_applied:
            return Response(
                {"detail": "This template has already been applied."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        period_str = request.data.get("period")
        if not period_str:
            return Response(
                {"detail": "period (YYYY-MM-DD) is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        count = apply_levy_template(template, period_str, request.user)
        return Response({
            "detail": f"Template applied. {count} member levies created.",
            "count": count,
        })


# ── Analytics ─────────────────────────────────────────────────

class AnalyticsDashboardView(views.APIView):
    permission_classes = [IsAuthenticated, IsFinancialSecretary]

    def get(self, request):
        from reports.services import community_summary
        summary = community_summary()

        # Top 10 contributors
        members = Member.objects.filter(status="ACTIVE")
        contributors = []
        for m in members:
            paid = m.total_levy_paid
            if paid > 0:
                contributors.append({
                    "id": m.pk,
                    "full_name": m.full_name,
                    "total_paid": paid,
                    "total_due": m.total_levy_due,
                })
        contributors.sort(key=lambda x: x["total_paid"], reverse=True)
        top10 = contributors[:10]

        # Defaulters
        defaulters = [
            {
                "id": m.pk,
                "full_name": m.full_name,
                "phone": m.phone,
                "outstanding_balance": m.outstanding_balance,
            }
            for m in members
            if m.is_defaulter
        ]
        defaulters.sort(key=lambda x: x["outstanding_balance"], reverse=True)

        # Monthly payment trend (last 12 months)
        from django.db.models.functions import TruncMonth
        trend = (
            Payment.objects
            .annotate(month=TruncMonth("payment_date"))
            .values("month")
            .annotate(total=Sum("amount"))
            .order_by("month")
        )
        trend_data = [
            {"month": t["month"].strftime("%Y-%m"), "total": str(t["total"])}
            for t in trend
        ]

        # Collection by levy type
        by_levy = (
            PaymentAllocation.objects
            .values("member_levy__levy__levy_type", "member_levy__levy__name")
            .annotate(total=Sum("amount_allocated"))
            .order_by("-total")
        )
        levy_breakdown = [
            {
                "levy_type": b["member_levy__levy__levy_type"],
                "levy_name": b["member_levy__levy__name"],
                "total_collected": str(b["total"]),
            }
            for b in by_levy
        ]

        return Response({
            "summary": summary,
            "top_contributors": top10,
            "defaulters": defaulters,
            "monthly_trend": trend_data,
            "collection_by_levy": levy_breakdown,
        })


class AnnouncementView(views.APIView):
    """Secretary broadcasts a message to all (or selected) active members."""
    permission_classes = [IsAuthenticated, IsFinancialSecretary]

    def post(self, request):
        title = request.data.get("title", "").strip()
        body = request.data.get("body", "").strip()
        if not title or not body:
            return Response(
                {"detail": "title and body are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        member_ids = request.data.get("member_ids", None)
        if member_ids is None:
            member_ids = list(
                Member.objects.filter(status="ACTIVE").values_list("pk", flat=True)
            )
        from notifications.tasks import broadcast_announcement
        broadcast_announcement.delay(title, body, member_ids)
        return Response({
            "detail": f"Announcement queued for {len(member_ids)} members."
        })
