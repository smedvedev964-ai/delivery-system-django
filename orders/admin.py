from django.contrib import admin
from .models import Order, OrderItem, OrderStatusHistory, Review
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = ("product_name", "quantity", "unit_price")

    def has_add_permission(self, request, obj=None): return False
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("number", "customer", "status", "total", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("number", "customer__email")
    inlines = [OrderItemInline]
    readonly_fields = ("number", "customer", "address", "address_snapshot", "status", "items_total", "delivery_fee", "total", "comment", "idempotency_key", "created_at", "updated_at")

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("order", "old_status", "new_status", "actor", "created_at")
    readonly_fields = ("order", "actor", "old_status", "new_status", "comment", "created_at")
    def has_add_permission(self, request): return False
    def has_delete_permission(self, request, obj=None): return False


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("order", "customer", "rating", "created_at")
    readonly_fields = ("order", "customer", "rating", "text", "created_at")
    def has_add_permission(self, request): return False
