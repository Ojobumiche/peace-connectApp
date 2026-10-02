from datetime import date, datetime
from decimal import Decimal

from django.test import TestCase

from members.models import Member
from payments.models import Payment, PaymentAllocation, PaymentMethod

from .models import Levy, LevyType, MemberLevy


class MemberLevyCalculationTests(TestCase):
	def setUp(self):
		self.member = Member.objects.create(
			first_name="John",
			last_name="Jeremiah",
			phone="08000000000",
			house_address="1 Peace Street",
		)
		self.levy = Levy.objects.create(
			name="Monthly Contribution",
			levy_type=LevyType.MONTHLY,
			amount=Decimal("50000.00"),
		)
		self.member_levy = MemberLevy.objects.create(
			member=self.member,
			levy=self.levy,
			period=date(2026, 8, 1),
			amount_due=Decimal("50000.00"),
		)

	def create_allocation(self, amount):
		payment = Payment.objects.create(
			member=self.member,
			amount=amount,
			payment_method=PaymentMethod.CASH,
			reference=f"PAY-{amount}",
			payment_date=datetime(2026, 8, 1),
		)
		return PaymentAllocation.objects.create(
			payment=payment,
			member_levy=self.member_levy,
			amount_allocated=amount,
		)

	def test_unpaid_levy(self):
		self.assertEqual(self.member_levy.amount_paid, Decimal("0.00"))
		self.assertEqual(self.member_levy.balance, Decimal("50000.00"))
		self.assertEqual(self.member_levy.status, "UNPAID")

	def test_partially_paid_levy(self):
		self.create_allocation(Decimal("20000.00"))

		self.assertEqual(self.member_levy.amount_paid, Decimal("20000.00"))
		self.assertEqual(self.member_levy.balance, Decimal("30000.00"))
		self.assertEqual(self.member_levy.status, "PARTIAL")

	def test_paid_levy(self):
		self.create_allocation(Decimal("50000.00"))

		self.assertEqual(self.member_levy.amount_paid, Decimal("50000.00"))
		self.assertEqual(self.member_levy.balance, Decimal("0.00"))
		self.assertEqual(self.member_levy.status, "PAID")

# Create your tests here.
