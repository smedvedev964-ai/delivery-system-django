from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Category, Product, Restaurant


RESTAURANTS = [
    {
        "name": "Додо Пицца", "slug": "dodo-pizza", "cuisine": "Пицца",
        "delivery_policy": "threshold", "delivery_fee": "149", "free_delivery_threshold": '999',
        "description": "Пицца, закуски и напитки. Демонстрационное меню учебного проекта.",
        "rating": "4.8", "rating_count": 2400, "delivery_min": 25, "delivery_max": 40,
        "image_url": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=900",
        "dishes": [
            ("Пицца Пепперони", "Пицца с пепперони и сыром.", "699", "Пицца", "https://images.unsplash.com/photo-1628840042765-356cda07504e?w=700"),
            ("Маргарита", "Томатный соус, моцарелла и базилик.", "549", "Пицца", "https://images.unsplash.com/photo-1579751626657-72bc17010498?w=700"),
            ("Картофельные дольки", "Запечённый картофель с приправами.", "199", "Закуски", "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=700"),
        ],
    },
    {
        "name": "Теремок", "slug": "teremok", "cuisine": "Русская кухня",
        "delivery_policy": "fixed", "delivery_fee": "99", "free_delivery_threshold": None,
        "description": "Блины, супы и горячие блюда русской кухни.",
        "rating": "4.7", "rating_count": 1300, "delivery_min": 30, "delivery_max": 45,
        "image_url": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=900",
        "dishes": [
            ("Блин с ветчиной и сыром", "Сытный блин с ветчиной и расплавленным сыром.", "289", "Блины", "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=700"),
            ("Блин с творогом", "Нежная творожная начинка.", "239", "Блины", "https://images.unsplash.com/photo-1528207776546-365bb710ee93?w=700"),
            ("Борщ", "Традиционный суп со сметаной.", "329", "Супы", "https://images.unsplash.com/photo-1547592180-85f173990554?w=700"),
        ],
    },
    {
        "name": "Шоколадница", "slug": "shokoladnitsa", "cuisine": "Кофейни и завтраки",
        "delivery_policy": "fixed", "delivery_fee": "149", "free_delivery_threshold": None,
        "description": "Кофе, завтраки, десерты и блюда на каждый день.",
        "rating": "4.6", "rating_count": 980, "delivery_min": 20, "delivery_max": 35,
        "image_url": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=900",
        "dishes": [
            ("Капучино", "Кофе на основе эспрессо и молока.", "249", "Напитки", "https://images.unsplash.com/photo-1534778101976-62847782c213?w=700"),
            ("Сырники", "Сырники со сметаной.", "359", "Завтраки", "https://images.unsplash.com/photo-1528207776546-365bb710ee93?w=700"),
            ("Чизкейк", "Нежный сливочный десерт.", "299", "Десерты", "https://images.unsplash.com/photo-1533134242443-d4fd215305ad?w=700"),
        ],
    },
    {
        "name": "MYBOX", "slug": "mybox", "cuisine": "Суши и роллы",
        "delivery_policy": "threshold", "delivery_fee": "199", "free_delivery_threshold": '1200',
        "description": "Роллы, суши и блюда азиатской кухни.",
        "rating": "4.7", "rating_count": 1600, "delivery_min": 45, "delivery_max": 60,
        "image_url": "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=900",
        "dishes": [
            ("Филадельфия", "Ролл с лососем, сливочным сыром и огурцом.", "589", "Роллы", "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=700"),
            ("Калифорния", "Ролл с крабом и авокадо.", "469", "Роллы", "https://images.unsplash.com/photo-1553621042-f6e147245754?w=700"),
            ("Мисо-суп", "Японский суп с тофу и водорослями.", "189", "Супы", "https://images.unsplash.com/photo-1607301406259-dfb186e15de8?w=700"),
        ],
    },
    {
        "name": "Крошка Картошка", "slug": "kroshka-kartoshka", "cuisine": "Русская кухня",
        "delivery_policy": "fixed", "delivery_fee": "129", "free_delivery_threshold": None,
        "description": "Запечённый картофель с разнообразными начинками.",
        "rating": "4.5", "rating_count": 760, "delivery_min": 25, "delivery_max": 40,
        "image_url": "https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=900",
        "dishes": [
            ("Картофель с сыром", "Запечённый картофель с сырной начинкой.", "349", "Горячее", "https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=700"),
            ("Картофель с грибами", "Картофель с грибами и зеленью.", "369", "Горячее", "https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=700"),
            ("Салат овощной", "Свежие овощи и зелень.", "229", "Салаты", "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=700"),
        ],
    },
    {
        "name": "Вкусно — и точка", "slug": "vkusno-i-tochka", "cuisine": "Бургеры",
        "delivery_policy": "fixed", "delivery_fee": "149", "free_delivery_threshold": None,
        "description": "Бургеры, картофель и напитки. Демонстрационные позиции меню.",
        "rating": "4.6", "rating_count": 2100, "delivery_min": 20, "delivery_max": 35,
        "image_url": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=900",
        "dishes": [
            ("Чизбургер", "Бургер с котлетой, сыром и соусом.", "249", "Бургеры", "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=700"),
            ("Картофель фри", "Хрустящий картофель фри.", "139", "Закуски", "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=700"),
            ("Куриные наггетсы", "Куриные кусочки в хрустящей панировке.", "229", "Закуски", "https://images.unsplash.com/photo-1562967914-608f82629710?w=700"),
        ],
    },
    {
        "name": "Rostic's", "slug": "rostics", "cuisine": "Курица и бургеры",
        "delivery_policy": "fixed", "delivery_fee": "149", "free_delivery_threshold": None,
        "description": "Блюда из курицы, сэндвичи и закуски.",
        "rating": "4.5", "rating_count": 1450, "delivery_min": 25, "delivery_max": 40,
        "image_url": "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?w=900",
        "dishes": [
            ("Куриные крылышки", "Крылышки в пряной панировке.", "359", "Курица", "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?w=700"),
            ("Бургер с курицей", "Куриная котлета, салат и соус.", "299", "Бургеры", "https://images.unsplash.com/photo-1606755962773-d324e0a13086?w=700"),
            ("Картофель фри", "Золотистый картофель фри.", "149", "Закуски", "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=700"),
        ],
    },
    {
        "name": "Суши Wok", "slug": "sushi-wok", "cuisine": "Азиатская кухня",
        "delivery_policy": "threshold", "delivery_fee": "179", "free_delivery_threshold": '900',
        "description": "Суши, роллы, лапша и горячие азиатские блюда.",
        "rating": "4.4", "rating_count": 890, "delivery_min": 40, "delivery_max": 55,
        "image_url": "https://images.unsplash.com/photo-1617196034796-73dfa7b1fd56?w=900",
        "dishes": [
            ("Запечённый ролл", "Ролл под нежной запечённой шапочкой.", "429", "Роллы", "https://images.unsplash.com/photo-1617196034796-73dfa7b1fd56?w=700"),
            ("Лапша с курицей", "Лапша с курицей и овощами.", "379", "Вок", "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=700"),
            ("Рис с овощами", "Рис с овощами в азиатском стиле.", "289", "Вок", "https://images.unsplash.com/photo-1603133872878-684f208fb84b?w=700"),
        ],
    },
]


class Command(BaseCommand):
    help = "Добавляет демонстрационные российские ресторанные сети и меню"

    @transaction.atomic
    def handle(self, *args, **options):
        created_restaurants = created_dishes = 0
        for data in RESTAURANTS:
            restaurant, created = Restaurant.objects.update_or_create(
                slug=data["slug"],
                defaults={key: value for key, value in data.items() if key != "dishes"},
            )
            created_restaurants += int(created)
            for name, description, price, category_name, image_url in data["dishes"]:
                category, _ = Category.objects.get_or_create(name=category_name)
                _, dish_created = Product.objects.get_or_create(
                    restaurant=restaurant,
                    name=name,
                    defaults={
                        "category": category,
                        "description": description,
                        "price": Decimal(price),
                        "image_url": image_url,
                        "stock": 100,
                        "is_active": True,
                    },
                )
                created_dishes += int(dish_created)

        self.stdout.write(self.style.SUCCESS(
            f"Готово: новых ресторанов — {created_restaurants}, "
            f"новых блюд — {created_dishes}."
        ))
