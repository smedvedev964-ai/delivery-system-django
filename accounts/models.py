from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        CLIENT = "client", "Клиент"
        COURIER = "courier", "Курьер"
        MANAGER = "manager", "Менеджер"
        ADMIN = "admin", "Администратор"
    email = models.EmailField("Электронная почта", unique=True)
    phone = models.CharField("Телефон", max_length=30, blank=True)
    role = models.CharField("Роль", max_length=20, choices=Role.choices, default=Role.CLIENT)
    def __str__(self): return self.get_full_name() or self.username

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    city = models.CharField("Город", max_length=100)
    street = models.CharField("Улица", max_length=150)
    house = models.CharField("Дом", max_length=30)
    apartment = models.CharField("Квартира", max_length=30, blank=True)
    comment = models.CharField("Комментарий", max_length=255, blank=True)
    is_default = models.BooleanField("Адрес по умолчанию", default=False)
    class Meta: ordering = ["-is_default", "city", "street"]
    def __str__(self): return f"{self.city}, {self.street}, {self.house}" 
