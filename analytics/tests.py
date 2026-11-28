from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Address
from catalog.models import Category, Product, Restaurant
from orders.models import Order, OrderItem
from .services import order_summary, popular_categories

User = get_user_model()


class AnalyticsTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="manager", email="analytics-manager@example.test",
            password="strong-test-password", role="manager",
        )
        self.customer = User.objects.create_user(
            username="customer", email="analytics-customer@example.test",
            password="strong-test-password", role="client",
        )
        self.address = Address.objects.create(
            user=self.customer, city="Москва", street="Тестовая", house="3"
        )
        self.restaurant = Restaurant.objects.create(
            name="Analytics Test", slug="analytics-test", cuisine="Test", rating="4.0"
        )
        self.category = Category.objects.create(name="Analytics Category")
        self.product = Product.objects.create(
            restaurant=self.restaurant, category=self.category, name="Analytics Meal",
            price=Decimal("100.00"), stock=10,
        )
        self.delivered = Order.objects.create(
            customer=self.customer, address=self.address,
            address_snapshot={"city": "Москва"}, status=Order.Status.DELIVERED,
            items_total=Decimal("200"), total=Decimal("200"),
        )
        self.pending = Order.objects.create(
            customer=self.customer, address=self.address,
            address_snapshot={"city": "Москва"}, status=Order.Status.PENDING,
            items_total=Decimal("300"), total=Decimal("300"),
        )
        OrderItem.objects.create(
            order=self.delivered, product=self.product, product_name=self.product.name,
            quantity=2, unit_price=Decimal("100"),
        )

    def test_reports_include_delivered_revenue_and_filter_date_range(self):
        today = timezone.localdate()
        summary = order_summary(today, today)
        self.assertEqual(summary["total_orders"], 2)
        self.assertEqual(summary["delivered_orders"], 1)
        self.assertEqual(summary["revenue"], Decimal("200"))
        self.assertEqual(summary["average_order"], Decimal("200"))
        categories = list(popular_categories(today, today))
        self.assertEqual(categories[0]["units_sold"], 2)
        self.assertEqual(categories[0]["revenue"], Decimal("200"))

        empty = order_summary(today.replace(year=today.year - 1), today.replace(year=today.year - 1))
        self.assertEqual(empty["total_orders"], 0)
        self.assertIsNone(empty["revenue"])

    def test_analytics_dashboard_is_staff_only_and_renders_period_form(self):
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(reverse("analytics:dashboard")).status_code, 403)

        self.client.force_login(self.manager)
        response = self.client.get(reverse("analytics:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Средний чек")
        self.assertIn("summary", response.context)
