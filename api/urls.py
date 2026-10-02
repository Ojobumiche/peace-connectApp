from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    LoginView, LogoutView, ChangePasswordView,
    MemberDashboardView, MyLeviesView, MyPaymentsView,
    MyCreditView, MyProfileView, MyNotificationsView,
    MarkNotificationReadView,
    MemberListView, LevyListCreateView,
    LevyTemplateListCreateView, LevyTemplateApplyView,
    AnalyticsDashboardView, AnnouncementView,
)

urlpatterns = [
    # ── Auth ──────────────────────────────────────────
    path("auth/login/", LoginView.as_view(), name="api-login"),
    path("auth/logout/", LogoutView.as_view(), name="api-logout"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="api-token-refresh"),
    path("auth/change-password/", ChangePasswordView.as_view(), name="api-change-password"),

    # ── Member portal (own data) ───────────────────────
    path("me/dashboard/", MemberDashboardView.as_view(), name="api-dashboard"),
    path("me/levies/", MyLeviesView.as_view(), name="api-my-levies"),
    path("me/payments/", MyPaymentsView.as_view(), name="api-my-payments"),
    path("me/credits/", MyCreditView.as_view(), name="api-my-credits"),
    path("me/profile/", MyProfileView.as_view(), name="api-my-profile"),
    path("me/notifications/", MyNotificationsView.as_view(), name="api-my-notifications"),
    path("me/notifications/<int:pk>/read/", MarkNotificationReadView.as_view(), name="api-notif-read"),

    # ── Staff / Secretary ──────────────────────────────
    path("members/", MemberListView.as_view(), name="api-members"),
    path("levies/", LevyListCreateView.as_view(), name="api-levies"),
    path("levy-templates/", LevyTemplateListCreateView.as_view(), name="api-levy-templates"),
    path("levy-templates/<int:pk>/apply/", LevyTemplateApplyView.as_view(), name="api-levy-template-apply"),

    # ── Analytics ──────────────────────────────────────
    path("analytics/", AnalyticsDashboardView.as_view(), name="api-analytics"),
    path("announcements/", AnnouncementView.as_view(), name="api-announcement"),
]
