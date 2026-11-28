from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.text import slugify


class Restaurant(models.Model):
    name = models.CharField("Название ресторана", max_length=160, unique=True)
    slug = models.SlugField("Адрес страницы", max_length=180, unique=True)
    description = models.TextField("Описание", blank=True)
    cuisine = models.CharField("Кухня", max_length=80, db_index=True)
    address = models.CharField("Адрес", max_length=255, blank=True)
    image_url = models.URLField("Фотография ресторана", blank=True)
    logo_url = models.URLField("Логотип", blank=True)
    rating = models.DecimalField(
        "Рейтинг", max_digits=2, decimal_places=1,
        default=0, validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    rating_count = models.PositiveIntegerField("Количество оценок", default=0)
    delivery_min = models.PositiveSmallIntegerField("Минимальное время доставки", default=30)
    delivery_max = models.PositiveSmallIntegerField("Максимальное время доставки", default=45)
    class DeliveryPolicy(models.TextChoices):
        FIXED = "fixed", "Фиксированная стоимость"
        FREE = "free", "Бесплатная доставка"
        THRESHOLD = "threshold", "Бесплатно от суммы заказа"

    delivery_policy = models.CharField(
        "Условия доставки", max_length=12,
        choices=DeliveryPolicy.choices, default=DeliveryPolicy.FIXED,
    )
    delivery_fee = models.DecimalField(
        "Стоимость доставки", max_digits=8, decimal_places=2,
        default=149, validators=[MinValueValidator(0)]
    )
    free_delivery_threshold = models.DecimalField(
        "Порог бесплатной доставки", max_digits=10, decimal_places=2,
        null=True, blank=True, validators=[MinValueValidator(0)]
    )
    is_active = models.BooleanField("Работает", default=True)
    created_at = models.DateTimeField("Добавлен", auto_now_add=True)

    class Meta:
        ordering = ["-rating", "name"]
        verbose_name = "Ресторан"
        verbose_name_plural = "Рестораны"

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField("Название", max_length=120, unique=True)
    description = models.TextField("Описание", blank=True)
    is_active = models.BooleanField("Активна", default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Категория меню"
        verbose_name_plural = "Категории меню"

    def __str__(self):
        return self.name


class Product(models.Model):
    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.PROTECT, related_name="products",
        verbose_name="Ресторан", null=True, blank=True
    )
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="products",
        verbose_name="Категория"
    )
    name = models.CharField("Название", max_length=180)
    description = models.TextField("Описание", blank=True)
    price = models.DecimalField(
        "Цена", max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField("Изображение", upload_to="products/", blank=True)
    image_url = models.URLField("Ссылка на фотографию", blank=True)
    stock = models.PositiveIntegerField("Остаток", default=0)
    is_active = models.BooleanField("Активен", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Блюдо"
        verbose_name_plural = "Блюда"

    def __str__(self):
        return self.name
