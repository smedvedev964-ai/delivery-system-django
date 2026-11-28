from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Category, Product, Restaurant


RESTAURANTS = [
    {
        "name": "Додо Пицца", "slug": "dodo-pizza", "cuisine": "Пицца",
        "logo_url": "https://media.dodostatic.net/image/r:520x520/01980e8dad62703bb169ba6f96c60eb3.png",
        "delivery_policy": "threshold", "delivery_fee": "149", "free_delivery_threshold": '999',
        "description": "Пицца, закуски и напитки. Демонстрационное меню учебного проекта.",
        "rating": "4.8", "rating_count": 2400, "delivery_min": 25, "delivery_max": 40,
        "image_url": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=900",
        "dishes": [
            ("Пицца Пепперони", "Пицца с пепперони и сыром.", "699", "Пицца", "https://images.unsplash.com/photo-1628840042765-356cda07504e?w=700"),
            ("Маргарита", "Томатный соус, моцарелла и базилик.", "549", "Пицца", "https://images.unsplash.com/photo-1579751626657-72bc17010498?w=700"),
            ("Пицца Терияки", "Курица, соус терияки, моцарелла и кунжут.", "629", "Пицца", "https://media.dodostatic.net/image/r:292x292/0198bf24170179679a7872f2ddf16d18.png"),
            ("Пицца Мясная", "Пепперони, ветчина, цыплёнок и томатный соус.", "749", "Пицца", "https://media.dodostatic.net/image/r:520x520/0198bf3b88d5772695c7f9e557b5b196.png"),
            ("Пицца Цыплёнок барбекю", "Цыплёнок, моцарелла и соус барбекю.", "699", "Пицца", "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=700"),
            ("Пицца Четыре сыра", "Моцарелла и несколько видов сыра на сливочной основе.", "729", "Пицца", "https://media.dodostatic.net/image/r:292x292/01a1bf3e77be787eb8ffbd97709a33cb.jpg"),
            ("Картофельные дольки", "Запечённый картофель с приправами.", "199", "Закуски", "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=700"),
            ("Картофель из печи", "Запечённый картофель с пряностями.", "229", "Закуски", "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=700"),
            ("Додочизы", "Горячая сырная закуска с хрустящей корочкой.", "279", "Закуски", "https://images.unsplash.com/photo-1531749668029-2db88e4276c7?w=700"),
            ("Куриные наггетсы", "Куриные кусочки в хрустящей панировке.", "249", "Закуски", "https://images.unsplash.com/photo-1562967914-608f82629710?w=700"),
            ("Додо морс клюква", "Ягодный морс собственного приготовления.", "189", "Напитки", "https://images.unsplash.com/photo-1546173159-315724a31696?w=700"),
            ("Лимонад голубика-лайм", "Освежающий лимонад с голубикой и лаймом.", "159", "Напитки", "https://images.unsplash.com/photo-1513558161293-cdaf765edfd7?w=700"),
            ("Добрый Кола", "Газированный напиток, 0,5 л.", "155", "Напитки", "https://images.unsplash.com/photo-1629203851122-3726ecdf080e?w=700"),
            ("Шоколадный кукис", "Мягкое печенье с кусочками шоколада.", "119", "Десерты", "https://images.unsplash.com/photo-1499636136210-6f4ee915583e?w=700"),
            ("Пломбир Додокрошка", "Ванильное мороженое с шоколадной крошкой.", "169", "Десерты", "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=700"),
        ],
    },
    {
        "name": "Теремок", "slug": "teremok", "cuisine": "Русская кухня",
        "logo_url": "https://www.google.com/s2/favicons?domain=teremok.ru&sz=128",
        "delivery_policy": "fixed", "delivery_fee": "99", "free_delivery_threshold": None,
        "description": "Блины, супы и горячие блюда русской кухни.",
        "rating": "4.7", "rating_count": 1300, "delivery_min": 30, "delivery_max": 45,
        "image_url": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=900",
        "dishes": [
            ("Блин с ветчиной и сыром", "Сытный блин с ветчиной и расплавленным сыром.", "289", "Блины", "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=700"),
            ("Блин с творогом", "Нежная творожная начинка.", "239", "Блины", "https://images.unsplash.com/photo-1528207776546-365bb710ee93?w=700"),
            ("Блин с лососем и сырным кремом", "Слабосолёный лосось и нежный сливочный сыр.", "429", "Блины", "https://images.unsplash.com/photo-1519676867240-f03562e64548?w=700"),
            ("Блинчики с мясом", "Тонкие блины с сочной мясной начинкой.", "319", "Блины", "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=700"),
            ("Блины с творогом и вишней", "Творожная начинка с вишнёвым вареньем.", "279", "Блины", "https://images.unsplash.com/photo-1528207776546-365bb710ee93?w=700"),
            ("Блинчики с шоколадом", "Сладкие блины с шоколадной начинкой.", "259", "Блины", "https://images.unsplash.com/photo-1484723091739-30a097e8f929?w=700"),
            ("Борщ", "Традиционный суп со сметаной.", "329", "Супы", "https://images.unsplash.com/photo-1547592180-85f173990554?w=700"),
            ("Суп куриный с лапшой", "Куриный бульон, лапша и зелень.", "299", "Супы", "https://images.unsplash.com/photo-1547592180-85f173990554?w=700"),
            ("Солянка", "Наваристый суп с мясом и солёными огурцами.", "349", "Супы", "https://images.unsplash.com/photo-1547592180-85f173990554?w=700"),
            ("Каша овсяная", "Овсяная каша на молоке.", "219", "Завтраки", "https://images.unsplash.com/photo-1517673132405-a56a62b18caf?w=700"),
            ("Сырники со сметаной", "Творожные сырники со сметаной.", "329", "Завтраки", "https://images.unsplash.com/photo-1528207776546-365bb710ee93?w=700"),
            ("Морс ягодный", "Домашний морс из ягод.", "149", "Напитки", "https://images.unsplash.com/photo-1546173159-315724a31696?w=700"),
            ("Чай облепиховый", "Горячий чай с облепихой и мёдом.", "199", "Напитки", "https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=700"),
            ("Блинный десерт с яблоком", "Сладкие блинчики с яблочной начинкой.", "279", "Десерты", "https://images.unsplash.com/photo-1484723091739-30a097e8f929?w=700"),
        ],
    },
    {
        "name": "Шоколадница", "slug": "shokoladnitsa", "cuisine": "Кофейни и завтраки",
        "logo_url": "https://www.google.com/s2/favicons?domain=shoko.ru&sz=128",
        "delivery_policy": "fixed", "delivery_fee": "149", "free_delivery_threshold": None,
        "description": "Кофе, завтраки, десерты и блюда на каждый день.",
        "rating": "4.6", "rating_count": 980, "delivery_min": 20, "delivery_max": 35,
        "image_url": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=900",
        "dishes": [
            ("Капучино", "Кофе на основе эспрессо и молока.", "249", "Напитки", "https://images.unsplash.com/photo-1534778101976-62847782c213?w=700"),
            ("Сырники", "Сырники со сметаной.", "359", "Завтраки", "https://images.unsplash.com/photo-1528207776546-365bb710ee93?w=700"),
            ("Чизкейк", "Нежный сливочный десерт.", "299", "Десерты", "https://images.unsplash.com/photo-1533134242443-d4fd215305ad?w=700"),
            ("Английский завтрак", "Яйца, колбаски, картофель и тосты.", "549", "Завтраки", "https://images.unsplash.com/photo-1525351484163-7529414344d8?w=700"),
            ("Бенедикт с лососем", "Бриошь, яйцо пашот и слабосолёный лосось.", "629", "Завтраки", "https://images.unsplash.com/photo-1525351484163-7529414344d8?w=700"),
            ("Сырники с вишней", "Сырники с вишнёвым соусом и сладким муссом.", "399", "Завтраки", "https://images.unsplash.com/photo-1528207776546-365bb710ee93?w=700"),
            ("Салат Цезарь с цыплёнком", "Листья салата, цыплёнок, сыр и соус Цезарь.", "459", "Салаты", "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=700"),
            ("Борщ с мясом", "Борщ со сметаной и зеленью.", "389", "Супы", "https://images.unsplash.com/photo-1547592180-85f173990554?w=700"),
            ("Том Ям", "Острый суп с креветками и кокосовым молоком.", "549", "Супы", "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=700"),
            ("Паста Карбонара", "Паста со сливочным соусом и сыром.", "499", "Основные блюда", "https://images.unsplash.com/photo-1473093295043-cdd812d0e601?w=700"),
            ("Блины с лососем", "Тонкие блины со слабосолёным лососем.", "449", "Блинчики", "https://images.unsplash.com/photo-1519676867240-f03562e64548?w=700"),
            ("Раф Ириска", "Кофейный напиток с молоком и карамельной ноткой.", "349", "Кофе", "https://images.unsplash.com/photo-1534778101976-62847782c213?w=700"),
            ("Айс-латте", "Охлаждённый кофе с молоком.", "329", "Кофе", "https://images.unsplash.com/photo-1517701604599-bb29b565090c?w=700"),
            ("Чай облепиховый", "Горячий чай с облепихой.", "299", "Чай", "https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=700"),
            ("Лимонад маракуйя-апельсин", "Домашний цитрусовый лимонад.", "319", "Холодные напитки", "https://images.unsplash.com/photo-1513558161293-cdaf765edfd7?w=700"),
            ("Наполеон", "Слоёный десерт с нежным кремом.", "329", "Десерты", "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=700"),
        ],
    },
    {
        "name": "MYBOX", "slug": "mybox", "cuisine": "Суши и роллы",
        "logo_url": "https://www.google.com/s2/favicons?domain=mybox.ru&sz=128",
        "delivery_policy": "threshold", "delivery_fee": "199", "free_delivery_threshold": '1200',
        "description": "Роллы, суши и блюда азиатской кухни.",
        "rating": "4.7", "rating_count": 1600, "delivery_min": 45, "delivery_max": 60,
        "image_url": "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=900",
        "dishes": [
            ("Филадельфия", "Ролл с лососем, сливочным сыром и огурцом.", "589", "Роллы", "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=700"),
            ("Калифорния", "Ролл с крабом и авокадо.", "469", "Роллы", "https://images.unsplash.com/photo-1553621042-f6e147245754?w=700"),
            ("Мисо-суп", "Японский суп с тофу и водорослями.", "189", "Супы", "https://images.unsplash.com/photo-1607301406259-dfb186e15de8?w=700"),
            ("Филадельфия с угрём", "Ролл с угрём, сливочным сыром и огурцом.", "629", "Роллы", "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=700"),
            ("Ролл Калифорния с креветкой", "Креветка, авокадо и икра масаго.", "549", "Роллы", "https://images.unsplash.com/photo-1553621042-f6e147245754?w=700"),
            ("Запечённый ролл с лососем", "Ролл с лососем под запечённой сырной шапочкой.", "519", "Запечённые роллы", "https://images.unsplash.com/photo-1617196034796-73dfa7b1fd56?w=700"),
            ("Сет Филадельфия", "Ассорти популярных роллов с лососем.", "1199", "Сеты", "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=700"),
            ("Поке с лососем", "Рис, лосось, овощи и соус.", "599", "Поке и салаты", "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=700"),
            ("Лапша удон с курицей", "Удон с курицей и овощами в соусе терияки.", "429", "Лапша вок", "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=700"),
            ("Рис с курицей терияки", "Рис с курицей, овощами и соусом терияки.", "399", "Горячие блюда", "https://images.unsplash.com/photo-1603133872878-684f208fb84b?w=700"),
            ("Гёдза с курицей", "Японские пельмени с курицей.", "329", "Закуски", "https://images.unsplash.com/photo-1563240927-7ce3e8c4a549?w=700"),
            ("Том Ям с креветками", "Острый суп с креветками и кокосовым молоком.", "499", "Супы", "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=700"),
            ("Онигири с лососем", "Рисовый треугольник с начинкой из лосося.", "229", "Онигири", "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=700"),
            ("Чизкейк", "Нежный сливочный десерт.", "279", "Десерты", "https://images.unsplash.com/photo-1533134242443-d4fd215305ad?w=700"),
            ("Морс клюквенный", "Ягодный напиток собственного приготовления.", "159", "Напитки", "https://images.unsplash.com/photo-1546173159-315724a31696?w=700"),
        ],
    },
    {
        "name": "Крошка Картошка", "slug": "kroshka-kartoshka", "cuisine": "Русская кухня",
        "logo_url": "https://www.google.com/s2/favicons?domain=kartoshka.com&sz=128",
        "delivery_policy": "fixed", "delivery_fee": "129", "free_delivery_threshold": None,
        "description": "Запечённый картофель с разнообразными начинками.",
        "rating": "4.5", "rating_count": 760, "delivery_min": 25, "delivery_max": 40,
        "image_url": "https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=900",
        "dishes": [
            ("Картофель с сыром", "Запечённый картофель с сырной начинкой.", "349", "Горячее", "https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=700"),
            ("Картофель с грибами", "Картофель с грибами и зеленью.", "369", "Горячее", "https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=700"),
            ("Салат овощной", "Свежие овощи и зелень.", "229", "Салаты", "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=700"),
            ("Крошка Картошка со сливочным маслом", "Запечённый картофель со сливочным маслом и зеленью.", "289", "Картофель", "https://www.kartoshka.com/media/images/1600kh1200_mesh_malyi_1.height-440.jpg"),
            ("Печёный Мэш Классический", "Картофельное пюре с сырной заправкой и зеленью.", "249", "Картофель", "https://www.kartoshka.com/media/images/1600kh1200_mesh_malyi_1.height-440.jpg"),
            ("Гриль Чиз Креветки Том Ям", "Запечённый картофель, креветки и пряный соус том ям.", "499", "Гриль Чиз", "https://www.kartoshka.com/media/images/GCh_krevetki_belyi.height-440.jpg"),
            ("Гриль Чиз Корн бекон", "Запечённый картофель с кукурузой, беконом и сыром.", "449", "Гриль Чиз", "https://www.kartoshka.com/media/images/GCh_krevetki_belyi.height-440.jpg"),
            ("Гриль Чиз Куриный шашлык", "Картофель с курицей, овощами и сырной заправкой.", "469", "Гриль Чиз", "https://www.kartoshka.com/media/images/GCh_krevetki_belyi.height-440.jpg"),
            ("Картофель с крабовой начинкой", "Запечённый картофель с крабовой начинкой.", "399", "Картофель", "https://www.kartoshka.com/media/images/1600kh1200_mesh_malyi_1.height-440.jpg"),
            ("Суп гороховый", "Гороховый суп с копчёностями и зеленью.", "299", "Супы и горячее", "https://images.unsplash.com/photo-1547592180-85f173990554?w=700"),
            ("Суп чечевичный с курицей", "Чечевичный суп с курицей.", "329", "Супы и горячее", "https://images.unsplash.com/photo-1547592180-85f173990554?w=700"),
            ("Сэндвич с курицей", "Курица, свежие овощи и соус в тортилье.", "329", "Сэндвичи", "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?w=700"),
            ("Овощной салат", "Салат из свежих овощей и зелени.", "249", "Салаты", "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=700"),
            ("Морс клюквенный", "Ягодный морс собственного приготовления.", "149", "Напитки", "https://images.unsplash.com/photo-1546173159-315724a31696?w=700"),
            ("Чай облепиховый", "Горячий чай с облепихой.", "199", "Напитки", "https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=700"),
        ],
    },
    {
        "name": "Вкусно — и точка", "slug": "vkusno-i-tochka", "cuisine": "Бургеры",
        "logo_url": "https://vkusnoitochka.ru/pages/company/media/logo.png",
        "delivery_policy": "fixed", "delivery_fee": "149", "free_delivery_threshold": None,
        "description": "Бургеры, картофель и напитки. Демонстрационные позиции меню.",
        "rating": "4.6", "rating_count": 2100, "delivery_min": 20, "delivery_max": 35,
        "image_url": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=900",
        "dishes": [
            ("Чизбургер", "Бургер с котлетой, сыром и соусом.", "249", "Бургеры", "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=700"),
            ("Картофель фри", "Хрустящий картофель фри.", "139", "Закуски", "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=700"),
            ("Куриные наггетсы", "Куриные кусочки в хрустящей панировке.", "229", "Закуски", "https://images.unsplash.com/photo-1562967914-608f82629710?w=700"),
            ("Двойной чизбургер", "Две котлеты, сыр, огурцы и фирменный соус.", "329", "Бургеры", "https://images.unsplash.com/photo-1550547660-d9450f859349?w=700"),
            ("Биг Хит", "Бургер с говяжьей котлетой, сыром и овощами.", "329", "Бургеры", "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=700"),
            ("Биг Чикен Базиликовый", "Куриное филе, салат и базиликовый соус.", "359", "Бургеры", "https://images.unsplash.com/photo-1606755962773-d324e0a13086?w=700"),
            ("Чикен Карри Ролл", "Курица и овощи в пшеничной лепёшке с соусом карри.", "279", "Роллы", "https://images.unsplash.com/photo-1626700051175-6818013e1d4f?w=700"),
            ("Панини Тоскана", "Тёплый панини с курицей, сыром и томатами.", "319", "Сэндвичи", "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?w=700"),
            ("Картофель по-деревенски", "Картофельные дольки с приправами.", "169", "Картофель и снеки", "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=700"),
            ("Сырные палочки", "Сыр в хрустящей панировке.", "249", "Картофель и снеки", "https://images.unsplash.com/photo-1531749668029-2db88e4276c7?w=700"),
            ("Бабл-ти Розовый помело", "Холодный напиток с помело и шариками тапиоки.", "279", "Напитки", "https://images.unsplash.com/photo-1558857563-b371033873b8?w=700"),
            ("Бабл милк Жасмин-виноград", "Молочный чай с жасмином, виноградом и тапиокой.", "279", "Напитки", "https://images.unsplash.com/photo-1558857563-b371033873b8?w=700"),
            ("Лимонад Дольче манго", "Освежающий лимонад с манго.", "159", "Напитки", "https://images.unsplash.com/photo-1513558161293-cdaf765edfd7?w=700"),
            ("Айс Какао", "Охлаждённый какао-напиток.", "229", "Напитки", "https://images.unsplash.com/photo-1517701604599-bb29b565090c?w=700"),
            ("Венецианские пончики", "Небольшие пончики с сахарной пудрой.", "179", "Десерты", "https://images.unsplash.com/photo-1551024506-0cc1cafea0f4?w=700"),
            ("Тропическое пирожное", "Нежный десерт с тропическими фруктами.", "239", "Десерты", "https://images.unsplash.com/photo-1533134242443-d4fd215305ad?w=700"),
        ],
    },
    {
        "name": "Rostic's", "slug": "rostics", "cuisine": "Курица и бургеры",
        "logo_url": "https://www.google.com/s2/favicons?domain=rostics.ru&sz=128",
        "delivery_policy": "fixed", "delivery_fee": "149", "free_delivery_threshold": None,
        "description": "Блюда из курицы, сэндвичи и закуски.",
        "rating": "4.5", "rating_count": 1450, "delivery_min": 25, "delivery_max": 40,
        "image_url": "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?w=900",
        "dishes": [
            ("Куриные крылышки", "Крылышки в пряной панировке.", "359", "Курица", "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?w=700"),
            ("Бургер с курицей", "Куриная котлета, салат и соус.", "299", "Бургеры", "https://images.unsplash.com/photo-1606755962773-d324e0a13086?w=700"),
            ("Картофель фри", "Золотистый картофель фри.", "149", "Закуски", "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=700"),
            ("Шефбургер оригинальный", "Куриное филе в панировке, салат и фирменный соус.", "349", "Бургеры", "https://images.unsplash.com/photo-1606755962773-d324e0a13086?w=700"),
            ("Шефбургер острый", "Острый куриный бургер с салатом и соусом.", "359", "Бургеры", "https://images.unsplash.com/photo-1606755962773-d324e0a13086?w=700"),
            ("Шефролл Джуниор", "Курица, свежий салат и соус в пшеничной лепёшке.", "299", "Роллы", "https://images.unsplash.com/photo-1626700051175-6818013e1d4f?w=700"),
            ("Чизбургер Де Люкс", "Говяжья котлета, сыр и свежие овощи.", "329", "Бургеры", "https://images.unsplash.com/photo-1550547660-d9450f859349?w=700"),
            ("Мой Баскет со стрипсами", "Куриные стрипсы, картофель фри и соус.", "299", "Баскеты", "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?w=700"),
            ("Стрипсы оригинальные", "Куриное филе в хрустящей панировке.", "319", "Курица", "https://images.unsplash.com/photo-1562967914-608f82629710?w=700"),
            ("Байтсы", "Кусочки куриного филе в панировке.", "249", "Курица", "https://images.unsplash.com/photo-1562967914-608f82629710?w=700"),
            ("Наггетсы", "Куриные наггетсы с хрустящей корочкой.", "229", "Закуски", "https://images.unsplash.com/photo-1562967914-608f82629710?w=700"),
            ("Картофель по-деревенски", "Пряные картофельные дольки.", "179", "Закуски", "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=700"),
            ("Мороженое рожок", "Ванильное мороженое в хрустящем рожке.", "99", "Десерты", "https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=700"),
            ("Донат ваниль в шоколаде", "Пончик с ванильной начинкой и шоколадной глазурью.", "179", "Десерты", "https://images.unsplash.com/photo-1551024506-0cc1cafea0f4?w=700"),
            ("Лимонад", "Освежающий газированный напиток.", "159", "Напитки", "https://images.unsplash.com/photo-1513558161293-cdaf765edfd7?w=700"),
            ("Кофе капучино", "Эспрессо с молоком и молочной пеной.", "219", "Напитки", "https://images.unsplash.com/photo-1534778101976-62847782c213?w=700"),
        ],
    },
    {
        "name": "Суши Wok", "slug": "sushi-wok", "cuisine": "Азиатская кухня",
        "logo_url": "https://storage.yandexcloud.net/sushiwok-web-storage-prod/42e3e1d5-084d-4f04-baf2-ff7f695f0ae0/3ea7fd5c-80c7-47b2-812b-6f849a02d56a/web/menuLogo.svg",
        "delivery_policy": "threshold", "delivery_fee": "179", "free_delivery_threshold": '900',
        "description": "Суши, роллы, лапша и горячие азиатские блюда.",
        "rating": "4.4", "rating_count": 890, "delivery_min": 40, "delivery_max": 55,
        "image_url": "https://images.unsplash.com/photo-1617196034796-73dfa7b1fd56?w=900",
        "dishes": [
            ("Запечённый ролл", "Ролл под нежной запечённой шапочкой.", "429", "Роллы", "https://images.unsplash.com/photo-1617196034796-73dfa7b1fd56?w=700"),
            ("Лапша с курицей", "Лапша с курицей и овощами.", "379", "Вок", "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=700"),
            ("Рис с овощами", "Рис с овощами в азиатском стиле.", "289", "Вок", "https://images.unsplash.com/photo-1603133872878-684f208fb84b?w=700"),
            ("Набор Филадельфия", "Ассорти роллов с лососем и сливочным сыром.", "1199", "Наборы и комбо", "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=700"),
            ("Запечённый ролл с креветкой", "Ролл с креветкой под запечённым соусом.", "499", "Запечённые роллы", "https://images.unsplash.com/photo-1617196034796-73dfa7b1fd56?w=700"),
            ("Лосось суши", "Пара суши с лососем и рисом.", "249", "Суши", "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=700"),
            ("Креветка суши", "Суши с тигровой креветкой.", "249", "Суши", "https://images.unsplash.com/photo-1553621042-f6e147245754?w=700"),
            ("Пицца Пепперони", "Пицца с пепперони и сыром.", "499", "Пицца", "https://images.unsplash.com/photo-1628840042765-356cda07504e?w=700"),
            ("Салат с чукой", "Морские водоросли чука с кунжутным соусом.", "279", "Салаты и закуски", "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=700"),
            ("Удон с говядиной", "Пшеничная лапша, говядина и овощи в вок-соусе.", "449", "Вок", "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=700"),
            ("Мисо-суп с лососем", "Японский суп с лососем, тофу и водорослями.", "299", "Супы и горячее", "https://images.unsplash.com/photo-1607301406259-dfb186e15de8?w=700"),
            ("Салат Цезарь", "Салат с курицей, сыром и соусом Цезарь.", "369", "Салаты и закуски", "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=700"),
            ("Ролл с огурцом", "Классический маки-ролл с огурцом.", "199", "Роллы", "https://images.unsplash.com/photo-1553621042-f6e147245754?w=700"),
            ("Чизкейк", "Нежный сливочный десерт.", "279", "Десерты и напитки", "https://images.unsplash.com/photo-1533134242443-d4fd215305ad?w=700"),
            ("Морс ягодный", "Ягодный морс.", "159", "Десерты и напитки", "https://images.unsplash.com/photo-1546173159-315724a31696?w=700"),
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
                defaults = {
                    "category": category,
                    "description": description,
                    "price": Decimal(price),
                    "image_url": image_url,
                    "stock": 100,
                    "is_active": True,
                }
                product, dish_created = Product.objects.get_or_create(
                    restaurant=restaurant,
                    name=name,
                    defaults=defaults,
                )
                if not dish_created:
                    for field, value in defaults.items():
                        if field != "stock":
                            setattr(product, field, value)
                    product.save(update_fields=[
                        field for field in defaults if field != "stock"
                    ])
                created_dishes += int(dish_created)

        self.stdout.write(self.style.SUCCESS(
            f"Готово: новых ресторанов — {created_restaurants}, "
            f"новых блюд — {created_dishes}."
        ))
