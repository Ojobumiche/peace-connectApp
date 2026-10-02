from django.db import models


class NotificationType(models.TextChoices):
    PAYMENT_RECEIVED = "PAYMENT_RECEIVED", "Payment Received"
    PAYMENT_RECEIPT = "PAYMENT_RECEIPT", "Payment Receipt"
    LEVY_ASSIGNED = "LEVY_ASSIGNED", "New Levy Assigned"
    LEVY_PAID = "LEVY_PAID", "Levy Fully Paid"
    DEBT_REMINDER = "DEBT_REMINDER", "Debt Reminder"
    CREDIT_APPROVED = "CREDIT_APPROVED", "Credit Approved"
    ANNOUNCEMENT = "ANNOUNCEMENT", "Community Announcement"


class NotificationChannel(models.TextChoices):
    EMAIL = "EMAIL", "Email"
    SMS = "SMS", "SMS"
    PUSH = "PUSH", "Push Notification"
    IN_APP = "IN_APP", "In-App"


class NotificationStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    SENT = "SENT", "Sent"
    FAILED = "FAILED", "Failed"
    READ = "READ", "Read"


class Notification(models.Model):
    """
    One row per notification delivery attempt per channel.
    """
    member = models.ForeignKey(
        "members.Member",
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
    )
    channel = models.CharField(
        max_length=10,
        choices=NotificationChannel.choices,
        default=NotificationChannel.IN_APP,
    )
    status = models.CharField(
        max_length=10,
        choices=NotificationStatus.choices,
        default=NotificationStatus.PENDING,
    )
    title = models.CharField(max_length=200)
    body = models.TextField()

    # Optional link back to the triggering object
    payment_id = models.PositiveIntegerField(null=True, blank=True)
    levy_id = models.PositiveIntegerField(null=True, blank=True)

    is_read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.member} — {self.notification_type} [{self.status}]"
