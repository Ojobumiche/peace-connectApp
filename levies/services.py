from django.utils import timezone
from .models import Levy, LevyTemplate, MemberLevy
from members.models import Member


def apply_levy_template(template: LevyTemplate, period_str: str, user=None) -> int:
    """
    Create a Levy from the template (if not yet a Levy) and assign
    a MemberLevy to every active member for the given period.

    Returns the number of MemberLevy records created.
    """
    from datetime import date
    period = date.fromisoformat(period_str)

    # Create or reuse the Levy record
    levy, _ = Levy.objects.get_or_create(
        name=template.name,
        defaults={
            "levy_type": template.levy_type,
            "category": template.category,
            "amount": template.amount,
            "description": template.description,
        },
    )

    active_members = Member.objects.filter(status=Member.Status.ACTIVE)
    created = 0

    for member in active_members:
        _, was_created = MemberLevy.objects.get_or_create(
            member=member,
            levy=levy,
            period=period,
            defaults={"amount_due": template.amount},
        )
        if was_created:
            created += 1
            # Trigger notification (async)
            from notifications.tasks import send_levy_assigned_notification
            ml = MemberLevy.objects.get(member=member, levy=levy, period=period)
            send_levy_assigned_notification.delay(ml.pk)

    # Mark template as applied
    template.is_applied = True
    template.applied_at = timezone.now()
    template.applied_by = user
    template.save(update_fields=["is_applied", "applied_at", "applied_by"])

    return created
