"""
Django signals that trigger notifications automatically on
payment save and credit approval — no manual wiring needed.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


@receiver(post_save, sender="payments.Payment")
def on_payment_saved(sender, instance, created, **kwargs):
    if not created:
        return
    from notifications.models import (
        Notification, NotificationType, NotificationChannel, NotificationStatus
    )
    from notifications.tasks import send_payment_receipt

    member = instance.member
    body = (
        f"Dear {member.first_name}, your payment of ₦{instance.amount:,.2f} "
        f"(Ref: {instance.reference}) has been received and recorded. "
        f"Thank you for your contribution to Peace CDA."
    )

    # In-app receipt (instant)
    Notification.objects.create(
        member=member,
        notification_type=NotificationType.PAYMENT_RECEIVED,
        channel=NotificationChannel.IN_APP,
        status=NotificationStatus.SENT,
        title="Payment Received",
        body=body,
        payment_id=instance.pk,
        sent_at=timezone.now(),
    )

    # Email receipt (async via Celery)
    if member.email:
        email_n = Notification.objects.create(
            member=member,
            notification_type=NotificationType.PAYMENT_RECEIPT,
            channel=NotificationChannel.EMAIL,
            title=f"Peace CDA Payment Receipt — {instance.reference}",
            body=body,
            payment_id=instance.pk,
        )
        send_payment_receipt.delay(email_n.pk)

    # SMS receipt (async via Celery)
    sms_n = Notification.objects.create(
        member=member,
        notification_type=NotificationType.PAYMENT_RECEIPT,
        channel=NotificationChannel.SMS,
        title="Peace CDA Payment Receipt",
        body=body,
        payment_id=instance.pk,
    )
    send_payment_receipt.delay(sms_n.pk)
