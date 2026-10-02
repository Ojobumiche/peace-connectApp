"""
Celery tasks for sending notifications.

In development (no Redis running) these tasks log to the console.
In production wire up Termii (SMS) and SendGrid (email).
"""
import logging
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)


# ── helpers ──────────────────────────────────────────────────

def _send_sms(phone: str, message: str):
    """Send SMS via Termii. Falls back to console log when key absent."""
    api_key = getattr(settings, "TERMII_API_KEY", "")
    if not api_key:
        logger.info("[SMS-STUB] To %s: %s", phone, message)
        return True
    try:
        import requests
        payload = {
            "to": phone,
            "from": settings.TERMII_SENDER_ID,
            "sms": message,
            "type": "plain",
            "api_key": api_key,
            "channel": "generic",
        }
        resp = requests.post(
            "https://api.ng.termii.com/api/sms/send",
            json=payload,
            timeout=10,
        )
        resp.raise_for_status()
        return True
    except Exception as exc:
        logger.error("[SMS] Failed to send to %s: %s", phone, exc)
        return False


def _mark_sent(notification_id: int, success: bool, error: str = ""):
    from notifications.models import Notification, NotificationStatus
    try:
        n = Notification.objects.get(pk=notification_id)
        n.status = NotificationStatus.SENT if success else NotificationStatus.FAILED
        n.sent_at = timezone.now() if success else None
        n.error_message = error
        n.save(update_fields=["status", "sent_at", "error_message"])
    except Notification.DoesNotExist:
        pass


# ── payment receipt ──────────────────────────────────────────

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_payment_receipt(self, notification_id: int):
    from notifications.models import Notification, NotificationChannel
    try:
        n = Notification.objects.select_related("member").get(pk=notification_id)
        member = n.member
        success = False

        if n.channel == NotificationChannel.EMAIL and member.email:
            try:
                send_mail(
                    subject=n.title,
                    message=n.body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[member.email],
                    fail_silently=False,
                )
                success = True
            except Exception as exc:
                logger.error("[EMAIL] %s", exc)
                _mark_sent(notification_id, False, str(exc))
                raise self.retry(exc=exc)

        elif n.channel == NotificationChannel.SMS:
            phone = member.whatsapp or member.phone
            success = _send_sms(phone, n.body)

        else:
            # IN_APP — already created in DB, just mark sent
            success = True

        _mark_sent(notification_id, success)

    except Notification.DoesNotExist:
        logger.warning("[TASK] Notification %s not found", notification_id)


# ── monthly debt reminder ─────────────────────────────────────

@shared_task
def send_monthly_debt_reminders():
    """
    Scheduled by Celery Beat (monthly).
    Sends SMS + in-app notification to every member with outstanding balance.
    """
    from members.models import Member
    from notifications.models import Notification, NotificationType, NotificationChannel, NotificationStatus

    debtors = [m for m in Member.objects.filter(status="ACTIVE") if m.is_defaulter]
    count = 0

    for member in debtors:
        balance = member.outstanding_balance
        body = (
            f"Dear {member.first_name}, this is a reminder that you owe "
            f"₦{balance:,.2f} to Peace CDA. "
            f"Please make your payment as soon as possible. Thank you."
        )
        # In-app
        Notification.objects.create(
            member=member,
            notification_type=NotificationType.DEBT_REMINDER,
            channel=NotificationChannel.IN_APP,
            status=NotificationStatus.SENT,
            title="Debt Reminder",
            body=body,
            sent_at=timezone.now(),
        )
        # SMS
        sms_notif = Notification.objects.create(
            member=member,
            notification_type=NotificationType.DEBT_REMINDER,
            channel=NotificationChannel.SMS,
            title="Debt Reminder",
            body=body,
        )
        send_payment_receipt.delay(sms_notif.pk)
        count += 1

    logger.info("[REMINDER] Sent debt reminders to %d members", count)
    return count


# ── levy assigned notification ────────────────────────────────

@shared_task
def send_levy_assigned_notification(member_levy_id: int):
    from levies.models import MemberLevy
    from notifications.models import Notification, NotificationType, NotificationChannel, NotificationStatus

    try:
        ml = MemberLevy.objects.select_related("member", "levy").get(pk=member_levy_id)
        member = ml.member
        body = (
            f"Dear {member.first_name}, a new levy has been assigned to you: "
            f"{ml.levy.name} — ₦{ml.amount_due:,.2f} "
            f"(Period: {ml.period.strftime('%B %Y')}). "
            f"Please log in to Peace CDA to view details."
        )
        n = Notification.objects.create(
            member=member,
            notification_type=NotificationType.LEVY_ASSIGNED,
            channel=NotificationChannel.IN_APP,
            status=NotificationStatus.SENT,
            title=f"New Levy: {ml.levy.name}",
            body=body,
            levy_id=ml.pk,
            sent_at=timezone.now(),
        )
        # Also send SMS
        sms_n = Notification.objects.create(
            member=member,
            notification_type=NotificationType.LEVY_ASSIGNED,
            channel=NotificationChannel.SMS,
            title=f"New Levy: {ml.levy.name}",
            body=body,
            levy_id=ml.pk,
        )
        send_payment_receipt.delay(sms_n.pk)
    except MemberLevy.DoesNotExist:
        pass


# ── announcement broadcast ────────────────────────────────────

@shared_task
def broadcast_announcement(title: str, body: str, member_ids: list):
    from members.models import Member
    from notifications.models import Notification, NotificationType, NotificationChannel, NotificationStatus

    members = Member.objects.filter(pk__in=member_ids)
    for member in members:
        n = Notification.objects.create(
            member=member,
            notification_type=NotificationType.ANNOUNCEMENT,
            channel=NotificationChannel.IN_APP,
            status=NotificationStatus.SENT,
            title=title,
            body=body,
            sent_at=timezone.now(),
        )
        if member.email:
            email_n = Notification.objects.create(
                member=member,
                notification_type=NotificationType.ANNOUNCEMENT,
                channel=NotificationChannel.EMAIL,
                title=title,
                body=body,
            )
            send_payment_receipt.delay(email_n.pk)
