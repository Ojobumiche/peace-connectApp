from decimal import Decimal

from django.db.models import Sum

from members.models import Member
from levies.models import MemberLevy
from payments.models import Payment


def community_summary():
    total_members = Member.objects.count()

    total_expected = (
        MemberLevy.objects.aggregate(
            total=Sum("amount_due")
        )["total"]
        or Decimal("0.00")
    )

    total_collected = (
        Payment.objects.aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    total_outstanding = total_expected - total_collected

    return {
        "total_members": total_members,
        "total_expected": total_expected,
        "total_collected": total_collected,
        "total_outstanding": total_outstanding,
    }
    