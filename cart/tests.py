from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from catalog.models import Category, Product, Restaurant
from .models import Cart, CartItem

User = get_user_model()


class CartWorkflowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="cart-user", email="cart-user@example.test",
            password="strong-test-password", role="client",
        )
        restaurant = Restaurant.objects.create(
            name="Cart Test", slug="cart-test", cuisine="Test", rating="4.0"
        )
        category = Category.objects.create(name="Cart Category")
        self.product = Product.objects.create(
            restaurant=restaurant, category=category, name="Cart meal",
            price=Decimal("120.00"), stock=2,
        )
        self.client.force_login(self.user)

    def test_ajax_add_and_quantity_controls_update_cart_without_page_redirect(self):
        url = reverse("cart:add", args=[self.product.pk])
        response = self.client.post(url, {"action": "increment"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["quantity"], 1)

        response = self.client.post(url, {"action": "increment"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["quantity"], 2)

        response = self.client.post(url, {"action": "increment"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(CartItem.objects.get(product=self.product).quantity, 2)

        item = CartItem.objects.get(product=self.product)
        response = self.client.post(
            reverse("cart:update", args=[item.pk]), {"action": "decrement"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CartItem.objects.get(pk=item.pk).quantity, 1)

        response = self.client.post(
            reverse("cart:update", args=[item.pk]), {"action": "decrement"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(CartItem.objects.filter(pk=item.pk).exists())

    def test_cart_actions_are_scoped_to_owner_and_clear_only_current_cart(self):
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        other = User.objects.create_user(
            username="other-cart-user", email="other-cart@example.test",
            password="strong-test-password", role="client",
        )
        self.client.force_login(other)
        response = self.client.post(reverse("cart:update", args=[item.pk]), {"action": "decrement"})
        self.assertEqual(response.status_code, 404)
        self.assertTrue(CartItem.objects.filter(pk=item.pk).exists())

        Cart.objects.create(user=other)
        response = self.client.post(reverse("cart:clear"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(CartItem.objects.filter(pk=item.pk).exists())
