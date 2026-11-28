from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import Address
from cart.models import Cart, CartItem
from catalog.models import Category, Product, Restaurant
from notifications.models import Notification
from .models import Order, OrderItem
from .services import change_order_status, create_order

User = get_user_model()


class OrderServiceTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            username="customer", email="customer@example.test", password="strong-test-password", role="client"
        )
        self.address = Address.objects.create(
            user=self.customer, city="Москва", street="Тестовая", house="10"
        )
        self.restaurant = Restaurant.objects.create(
            name="Тестовый ресторан", slug="test-restaurant", cuisine="Тест", rating="4.5"
        )
        self.category = Category.objects.create(name="Тестовая категория")
        self.product = Product.objects.create(
            restaurant=self.restaurant, category=self.category, name="Тестовое блюдо",
            price=Decimal("250.00"), stock=5,
        )
        cart, _ = Cart.objects.get_or_create(user=self.customer)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)

    def test_create_order_is_idempotent_and_cancel_restores_stock_once(self):
        order, created = create_order(
            user=self.customer, address=self.address, idempotency_key="same-checkout-request"
        )
        repeated, created_again = create_order(
            user=self.customer, address=self.address, idempotency_key="same-checkout-request"
        )

        self.assertTrue(created)
        self.assertFalse(created_again)
        self.assertEqual(order.pk, repeated.pk)
        self.assertEqual(Product.objects.get(pk=self.product.pk).stock, 3)
        self.assertEqual(order.items.get().unit_price, Decimal("250.00"))

        change_order_status(order=order, actor=self.customer, new_status=Order.Status.CANCELLED)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)
        self.assertTrue(Notification.objects.filter(user=self.customer, title="Статус заказа изменён").exists())

        with self.assertRaises(ValidationError):
            change_order_status(order=order, actor=self.customer, new_status=Order.Status.CANCELLED)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)

    def test_order_history_and_detail_are_scoped_to_customer(self):
        other = User.objects.create_user(
            username="other", email="other@example.test", password="strong-test-password", role="client"
        )
        other_address = Address.objects.create(
            user=other, city="Москва", street="Другая", house="2"
        )
        order = Order.objects.create(
            customer=self.customer, address=self.address,
            address_snapshot={"city": "Москва"}, total=Decimal("500.00"),
        )
        Order.objects.create(
            customer=other, address=other_address,
            address_snapshot={"city": "Москва"}, total=Decimal("100.00"),
        )

        self.client.force_login(self.customer)
        history = self.client.get(reverse("orders:history"))
        self.assertEqual(history.status_code, 200)
        self.assertContains(history, order.number)
        self.assertEqual(history.context["orders"].count(), 1)
        self.assertEqual(self.client.get(reverse("orders:detail", args=[Order.objects.exclude(customer=self.customer).get().pk])).status_code, 404)

    def test_idempotency_key_cannot_be_reused_by_another_customer(self):
        create_order(
            user=self.customer, address=self.address, idempotency_key="owned-checkout-key"
        )
        other = User.objects.create_user(
            username="other-key-user", email="other-key@example.test",
            password="strong-test-password", role="client",
        )
        other_address = Address.objects.create(
            user=other, city="Москва", street="Другая", house="9"
        )
        with self.assertRaises(PermissionDenied):
            create_order(user=other, address=other_address, idempotency_key="owned-checkout-key")

    def test_cancel_action_restores_inventory_and_is_not_available_after_preparing(self):
        order = Order.objects.create(
            customer=self.customer, address=self.address,
            address_snapshot={"city": "Москва"}, status=Order.Status.PREPARING,
        )
        OrderItem.objects.create(
            order=order, product=self.product, product_name=self.product.name,
            quantity=1, unit_price=self.product.price,
        )
        self.client.force_login(self.customer)
        response = self.client.post(
            reverse("orders:detail", args=[order.pk]), {"action": "cancel"}
        )
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PREPARING)
        self.assertEqual(Product.objects.get(pk=self.product.pk).stock, 5)

    def test_review_requires_delivered_order_and_can_only_be_submitted_once(self):
        order = Order.objects.create(
            customer=self.customer, address=self.address,
            address_snapshot={"city": "Москва"}, status=Order.Status.DELIVERED,
        )
        OrderItem.objects.create(
            order=order, product=self.product, product_name=self.product.name,
            quantity=1, unit_price=self.product.price,
        )
        self.client.force_login(self.customer)
        url = reverse("orders:detail", args=[order.pk])
        response = self.client.post(url, {"action": "review", "rating": "5", "text": "Всё отлично"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(order.review.rating, 5)
        self.restaurant.refresh_from_db()
        self.assertEqual(self.restaurant.rating, Decimal("5.0"))
        self.assertEqual(self.restaurant.rating_count, 1)

        response = self.client.post(url, {"action": "review", "rating": "4", "text": "Повтор"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(order.review.rating, 5)

    def test_customer_cannot_open_manager_panel(self):
        self.client.force_login(self.customer)
        response = self.client.get(reverse("orders:manager"))
        self.assertEqual(response.status_code, 403)

    def test_manager_panel_uses_allowed_transitions(self):
        order = Order.objects.create(
            customer=self.customer, address=self.address,
            address_snapshot={"city": "Москва", "street": "Тестовая", "house": "10"},
        )
        manager = User.objects.create_user(
            username="manager", email="manager@example.test",
            password="strong-test-password", role="manager",
        )
        self.client.force_login(manager)
        page = self.client.get(reverse("orders:manager"))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, order.number)

        updated = self.client.post(reverse("orders:manager"), {
            "action": "status", "order_id": order.pk, "status": Order.Status.CONFIRMED,
        })
        self.assertEqual(updated.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CONFIRMED)

        rejected = self.client.post(reverse("orders:manager"), {
            "action": "status", "order_id": order.pk, "status": Order.Status.DELIVERED,
        })
        self.assertEqual(rejected.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CONFIRMED)

