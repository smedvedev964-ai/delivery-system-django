from django.contrib import admin

from .models import Category, Product, Restaurant


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = (
        "name", "cuisine", "rating", "delivery_policy",
        "delivery_fee", "free_delivery_threshold", "is_active",
    )
    list_filter = ("cuisine", "delivery_policy", "is_active")
    search_fields = ("name", "description", "address")
    prepopulated_fields = {"slug": ("name",)}
    fieldsets = (
        ("Основная информация", {
            "fields": ("name", "slug", "description", "cuisine", "address", "image_url", "is_active"),
        }),
        ("Рейтинг и доставка", {
            "fields": (
                "rating", "rating_count", "delivery_min", "delivery_max",
                "delivery_policy", "delivery_fee", "free_delivery_threshold",
            ),
        }),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "restaurant", "category", "price", "stock", "is_active")
    list_filter = ("restaurant", "category", "is_active")
    search_fields = ("name", "description")
