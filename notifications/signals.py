"""
Django signals — fire notifications when a Payment is saved.

All Celery .delay() calls are wrapped in try/except so that if
Redis / the broker is not running, the in-app notification is still
saved and the admin save never crashes.
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

logger = logging.getLogger(__name__)


def _dispatch(task_fn, *args, **kwargs):
    """
    Call task.delay() safely.
    If the broker is unavailable the task runs synchronously (ALWAYS_EAGER=True
    in dev) or is silently skipped — the in-app Notification row is already
    saved so nothing is lost.
    """
    try:
        task_fn.delay(*args, **kwargs)
    except Exception as exc:
        logger.warning(
            "Could not queue notification task %s: %s — "
            "start Celery/Redis to enable async delivery.",
            task_fn.__name__, exc,
        )


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
        f"Dear {member.first_name}, your payment of "
        f"₦{instance.amount:,.2f} "
        f"(Ref: {instance.reference}) has been received and recorded. "
        f"Thank you for your contribution to Peace CDA."
    )

    # ── In-app notification (always instant, no broker needed) ──
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

    # ── Email receipt (async — safe if broker is down) ──────────
    if member.email:
        email_n = Notification.objects.create(
            member=member,
            notification_type=NotificationType.PAYMENT_RECEIPT,
            channel=NotificationChannel.EMAIL,
            title=f"Peace CDA Payment Receipt — {instance.reference}",
            body=body,
            payment_id=instance.pk,
        )
        _dispatch(send_payment_receipt, email_n.pk)

    # ── SMS receipt (async — safe if broker is down) ────────────
    sms_n = Notification.objects.create(
        member=member,
        notification_type=NotificationType.PAYMENT_RECEIPT,
        channel=NotificationChannel.SMS,
        title="Peace CDA Payment Receipt",
        body=body,
        payment_id=instance.pk,
    )
    _dispatch(send_payment_receipt, sms_n.pk)
