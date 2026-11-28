from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from accounts.models import Address
from catalog.models import Category, Product, Restaurant
from notifications.models import Notification
from orders.models import Order, OrderStatusHistory
from orders.services import change_order_status
from .models import CourierProfile, Delivery
from .services import assign_courier

User = get_user_model()


class DeliveryWorkflowTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            username="buyer", email="buyer@example.test", password="strong-test-password", role="client"
        )
        self.address = Address.objects.create(
            user=self.customer, city="Москва", street="Тестовая", house="1"
        )
        self.manager = User.objects.create_user(
            username="manager", email="manager@example.test", password="strong-test-password", role="manager"
        )
        self.courier = User.objects.create_user(
            username="courier", email="courier@example.test", password="strong-test-password", role="courier"
        )
        self.profile = CourierProfile.objects.create(
            user=self.courier, is_available=True, max_active_deliveries=1
        )
        restaurant = Restaurant.objects.create(
            name="Delivery Test", slug="delivery-test", cuisine="Test", rating="4.0"
        )
        category = Category.objects.create(name="Delivery Category")
        self.product = Product.objects.create(
            restaurant=restaurant, category=category, name="Meal", price=Decimal("100"), stock=10
        )
        self.order = self.make_order("first")

    def make_order(self, suffix):
        return Order.objects.create(
            number=f"ORD-{suffix.upper()}", customer=self.customer, address=self.address,
            address_snapshot={"city": "Москва", "street": "Тестовая", "house": "1"},
            status=Order.Status.PREPARING,
        )

    def test_assignment_and_courier_status_flow_is_audited(self):
        delivery = assign_courier(order=self.order, courier=self.courier, manager=self.manager)
        self.assertEqual(delivery.order_id, self.order.pk)
        self.assertEqual(self.order.__class__.objects.get(pk=self.order.pk).status, Order.Status.COURIER_ASSIGNED)
        self.assertTrue(Notification.objects.filter(user=self.customer, title="Курьер назначен").exists())

        for status in (Order.Status.HANDED_TO_COURIER, Order.Status.IN_TRANSIT, Order.Status.DELIVERED):
            change_order_status(order=self.order, actor=self.courier, new_status=status)

        delivery.refresh_from_db()
        self.assertFalse(delivery.is_current)
        self.assertIsNotNone(delivery.completed_at)
        self.assertEqual(OrderStatusHistory.objects.filter(order=self.order).count(), 4)

    def test_courier_capacity_and_assignment_ownership_are_enforced(self):
        assign_courier(order=self.order, courier=self.courier, manager=self.manager)
        second_order = self.make_order("second")
        with self.assertRaises(ValidationError):
            assign_courier(order=second_order, courier=self.courier, manager=self.manager)

        other_courier = User.objects.create_user(
            username="other-courier", email="other-courier@example.test",
            password="strong-test-password", role="courier",
        )
        with self.assertRaises(ValidationError):
            assign_courier(order=second_order, courier=other_courier, manager=self.manager)

    def test_courier_cannot_update_delivery_not_assigned_to_them(self):
        assign_courier(order=self.order, courier=self.courier, manager=self.manager)
        other = User.objects.create_user(
            username="other-courier", email="other-courier@example.test",
            password="strong-test-password", role="courier",
        )
        with self.assertRaises(PermissionDenied):
            change_order_status(order=self.order, actor=other, new_status=Order.Status.HANDED_TO_COURIER)

    def test_courier_dashboard_shows_only_the_logged_in_couriers_deliveries(self):
        assign_courier(order=self.order, courier=self.courier, manager=self.manager)
        self.client.force_login(self.courier)
        response = self.client.get("/delivery/courier/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.order.number)
        self.assertEqual(response.context["active_deliveries"].count(), 1)

