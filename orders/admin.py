from django.contrib import admin
from .models import Order, OrderItem, OrderStatusHistory, Review
class OrderItemInline(admin.TabularInline): model = OrderItem; extra = 0; readonly_fields = ("product_name", "quantity", "unit_price")
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin): list_display = ("number", "customer", "status", "total", "created_at"); list_filter = ("status", "created_at"); search_fields = ("number", "customer__email"); inlines = [OrderItemInline]
admin.site.register(OrderStatusHistory); admin.site.register(Review)
