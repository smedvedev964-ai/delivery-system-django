from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from orders.models import Order

class CourierProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="courier_profile")
    is_available = models.BooleanField(default=True)
    zone = models.CharField(max_length=100, blank=True)
    max_active_deliveries = models.PositiveSmallIntegerField(default=3, validators=[MinValueValidator(1)])
    def __str__(self): return f"Курьер: {self.user}"

class Delivery(models.Model):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="deliveries")
    courier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="deliveries")
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="assigned_deliveries")
    assigned_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_current = models.BooleanField(default=True)
    class Meta: ordering = ["-assigned_at"]
    def __str__(self): return f"{self.order.number} → {self.courier}"
