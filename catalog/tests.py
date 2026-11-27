from django.test import TestCase
from django.urls import reverse

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
