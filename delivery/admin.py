from django.contrib import admin
from .models import CourierProfile, Delivery


@admin.register(CourierProfile)
class CourierProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "is_available", "zone", "max_active_deliveries")
    list_filter = ("is_available", "zone")
    search_fields = ("user__username", "user__first_name", "user__last_name")


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ("order", "courier", "assigned_by", "assigned_at", "is_current")
    list_filter = ("is_current", "assigned_at")
    readonly_fields = ("order", "courier", "assigned_by", "assigned_at", "completed_at", "is_current")
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
