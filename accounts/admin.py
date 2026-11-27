from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Address
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Данные системы доставки", {"fields": ("phone", "role")}),)
    list_display = ("username", "email", "first_name", "last_name", "role", "is_active")
    list_filter = ("role", "is_active")
admin.site.register(Address)
