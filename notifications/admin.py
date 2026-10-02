from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "member", "notification_type", "channel",
        "status", "title", "sent_at", "is_read", "created_at",
    )
    list_filter = ("notification_type", "channel", "status", "is_read")
    search_fields = ("member__first_name", "member__last_name", "title")
    readonly_fields = ("sent_at", "read_at", "created_at", "error_message")
