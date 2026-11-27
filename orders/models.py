from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

def generate_order_number():
    return "ORD-" + uuid.uuid4().hex[:12].upper()
from accounts.models import Address
from catalog.models import Product

class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает подтверждения"
        CONFIRMED = "confirmed", "Подтверждён"
        PREPARING = "preparing", "Собирается"
        COURIER_ASSIGNED = "courier_assigned", "Назначен курьер"
        HANDED_TO_COURIER = "handed_to_courier", "Передан курьеру"
        IN_TRANSIT = "in_transit", "В пути"
        DELIVERED = "delivered", "Доставлен"
        CANCELLED = "cancelled", "Отменён"
        FAILED = "failed", "Не удалось доставить"
        RETURNED = "returned", "Возвращён"
    number = models.CharField("Номер заказа", max_length=24, unique=True, default=generate_order_number)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders")
    address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name="orders")
    address_snapshot = models.JSONField("Адрес на момент заказа", default=dict)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING, db_index=True)
    items_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    comment = models.TextField(blank=True)
    idempotency_key = models.CharField(max_length=64, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: ordering = ["-created_at"]
    def __str__(self): return self.number

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    product_name = models.CharField(max_length=180)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    @property
    def line_total(self): return self.unit_price * self.quantity

class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_history")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    old_status = models.CharField(max_length=30, blank=True)
    new_status = models.CharField(max_length=30, choices=Order.Status.choices)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["created_at"]

class Review(models.Model):
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="review")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
