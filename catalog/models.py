from django.db import models
from django.core.validators import MinValueValidator

class Category(models.Model):
    name = models.CharField("Название", max_length=120, unique=True)
    description = models.TextField("Описание", blank=True)
    is_active = models.BooleanField("Активна", default=True)
    def __str__(self): return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    name = models.CharField("Название", max_length=180)
    description = models.TextField("Описание", blank=True)
    price = models.DecimalField("Цена", max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    image = models.ImageField("Изображение", upload_to="products/", blank=True)
    stock = models.PositiveIntegerField("Остаток", default=0)
    is_active = models.BooleanField("Активен", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["name"]
    def __str__(self): return self.name
