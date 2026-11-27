from django.contrib import admin
from .models import Category, Product, Restaurant


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ("name", "cuisine", "rating", "is_active")
    list_filter = ("cuisine", "is_active")
    search_fields = ("name", "description", "address")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "restaurant", "category", "price", "stock", "is_active")
    list_filter = ("restaurant", "category", "is_active")
    search_fields = ("name", "description")
