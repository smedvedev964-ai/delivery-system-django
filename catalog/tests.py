from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from decimal import Decimal

from accounts.models import Address
from orders.models import Order, OrderItem
from orders.services import calculate_delivery_fee

from .models import Category, Product, Restaurant


class RestaurantCatalogTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.restaurant = Restaurant.objects.create(
            name="Тестовая пиццерия",
            slug="test-pizza",
            cuisine="Пицца",
            description="Тестовое описание",
            rating="4.8",
            delivery_min=25,
            delivery_max=40,
        )
        cls.other_restaurant = Restaurant.objects.create(
            name="Тестовое суши",
            slug="test-sushi",
            cuisine="Суши",
            rating="4.5",
        )
        cls.category = Category.objects.create(name="Пицца")
        cls.drinks = Category.objects.create(name="Напитки")
        cls.pizza = Product.objects.create(
            restaurant=cls.restaurant,
            category=cls.category,
            name="Маргарита",
            description="Пицца с сыром и томатами",
            price="550.00",
            stock=8,
        )
        cls.cola = Product.objects.create(
            restaurant=cls.restaurant,
            category=cls.drinks,
            name="Кола",
            price="150.00",
            stock=5,
        )
        cls.sushi = Product.objects.create(
            restaurant=cls.other_restaurant,
            category=cls.category,
            name="Ролл",
            price="400.00",
            stock=5,
        )

    def test_delivery_fee_rules(self):
        self.restaurant.delivery_policy = Restaurant.DeliveryPolicy.FIXED
        self.restaurant.delivery_fee = Decimal("99.00")
        self.assertEqual(
            calculate_delivery_fee(
                restaurant=self.restaurant,
                subtotal=Decimal("500.00"),
            ),
            Decimal("99.00"),
        )

        self.restaurant.delivery_policy = Restaurant.DeliveryPolicy.THRESHOLD
        self.restaurant.free_delivery_threshold = Decimal("900.00")
        self.assertEqual(
            calculate_delivery_fee(
                restaurant=self.restaurant,
                subtotal=Decimal("500.00"),
            ),
            Decimal("99.00"),
        )
        self.assertEqual(
            calculate_delivery_fee(
                restaurant=self.restaurant,
                subtotal=Decimal("900.00"),
            ),
            Decimal("0.00"),
        )

        self.restaurant.delivery_policy = Restaurant.DeliveryPolicy.FREE
        self.assertEqual(
            calculate_delivery_fee(
                restaurant=self.restaurant,
                subtotal=Decimal("10.00"),
            ),
            Decimal("0.00"),
        )

    def test_popularity_and_rating_sorts_use_different_metrics(self):
        user = get_user_model().objects.create_user(
            username="sort-test",
            email="sort-test@example.com",
            password="test-password-123",
        )
        address = Address.objects.create(
            user=user,
            city="Москва",
            street="Тестовая",
            house="1",
        )
        order = Order.objects.create(
            customer=user,
            address=address,
            address_snapshot={"city": "Москва"},
        )
        for _ in range(4):
            OrderItem.objects.create(
                order=order,
                product=self.sushi,
                product_name=self.sushi.name,
                quantity=1,
                unit_price=self.sushi.price,
            )

        popular = self.client.get(reverse("home"), {"sort": "popular"})
        rating = self.client.get(reverse("home"), {"sort": "rating"})

        popular_names = [item.name for item in popular.context["restaurants"]]
        rating_names = [item.name for item in rating.context["restaurants"]]

        self.assertLess(
            popular_names.index("Тестовое суши"),
            popular_names.index("Тестовая пиццерия"),
        )
        self.assertLess(
            rating_names.index("Тестовая пиццерия"),
            rating_names.index("Тестовое суши"),
        )

    def test_delivery_policy_is_visible_on_restaurant_page(self):
        self.restaurant.delivery_policy = Restaurant.DeliveryPolicy.THRESHOLD
        self.restaurant.delivery_fee = Decimal("120.00")
        self.restaurant.free_delivery_threshold = Decimal("900.00")
        self.restaurant.save()

        response = self.client.get(
            reverse("restaurant_detail", args=[self.restaurant.slug])
        )

        self.assertContains(response, "900")
        self.assertContains(response, "120")

    def test_home_shows_active_restaurants(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Тестовая пиццерия")
        self.assertContains(response, "Тестовое суши")

    def test_restaurant_search(self):
        response = self.client.get(reverse("home"), {"q": "пиццерия"})
        self.assertContains(response, "Тестовая пиццерия")
        self.assertNotContains(response, "Тестовое суши")

    def test_cuisine_filter(self):
        response = self.client.get(reverse("home"), {"cuisine": "Суши"})
        self.assertContains(response, "Тестовое суши")
        self.assertNotContains(response, "Тестовая пиццерия")

    def test_restaurant_page_shows_its_menu_only(self):
        response = self.client.get(
            reverse("restaurant_detail", args=[self.restaurant.slug])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Маргарита")
        self.assertContains(response, "Кола")
        self.assertNotContains(response, "Ролл")

    def test_menu_search(self):
        response = self.client.get(
            reverse("restaurant_detail", args=[self.restaurant.slug]),
            {"q": "сыром"},
        )
        self.assertContains(response, "Маргарита")
        self.assertNotContains(response, "Кола")

    def test_menu_category_filter(self):
        response = self.client.get(
            reverse("restaurant_detail", args=[self.restaurant.slug]),
            {"category": self.drinks.pk},
        )
        self.assertContains(response, "Кола")
        self.assertNotContains(response, "Маргарита")

    def test_product_detail_still_works(self):
        response = self.client.get(
            reverse("product_detail", args=[self.pizza.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Маргарита")

    def test_inactive_restaurant_is_not_public(self):
        self.restaurant.is_active = False
        self.restaurant.save(update_fields=["is_active"])
        response = self.client.get(
            reverse("restaurant_detail", args=[self.restaurant.slug])
        )
        self.assertEqual(response.status_code, 404)
