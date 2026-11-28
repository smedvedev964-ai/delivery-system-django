from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import Category, Product, Restaurant


class MenuFilterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.restaurant = Restaurant.objects.create(
            name="Меню тест", slug="menu-test", cuisine="Тест", rating="4.0"
        )
        cls.category = Category.objects.create(name="Тестовая категория")
        for index in range(26):
            Product.objects.create(
                restaurant=cls.restaurant,
                category=cls.category,
                name=f"Блюдо {index:02d}",
                price=Decimal(str(100 + index * 10)),
                stock=0 if index == 25 else 3,
            )

    def test_price_filter_and_sort(self):
        response = self.client.get(
            reverse("restaurant_detail", args=[self.restaurant.slug]),
            {"min_price": "150", "max_price": "180", "availability": "available", "sort": "price_desc"},
        )
        self.assertEqual(response.status_code, 200)
        products = response.context["products"]
        self.assertEqual([product.price for product in products], [Decimal("180"), Decimal("170"), Decimal("160"), Decimal("150")])

    def test_out_of_stock_filter_and_pagination_preserve_filters(self):
        url = reverse("restaurant_detail", args=[self.restaurant.slug])
        response = self.client.get(url, {"availability": "unavailable", "sort": "name"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([product.name for product in response.context["products"]], ["Блюдо 25"])

        response = self.client.get(url, {"availability": "available", "sort": "name", "page": "2"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].number, 2)
        self.assertIn("availability=available", response.context["query_string"])
        self.assertIn("sort=name", response.context["query_string"])

    def test_invalid_price_range_returns_no_products_and_explains_error(self):
        response = self.client.get(
            reverse("restaurant_detail", args=[self.restaurant.slug]),
            {"min_price": "400", "max_price": "100"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["products"])
        self.assertTrue(response.context["filter_errors"])
