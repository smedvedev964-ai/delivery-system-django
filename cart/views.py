from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from catalog.models import Product
from .models import Cart, CartItem


def _return_to(request, fallback):
    target = request.POST.get("next", "")
    if target and url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return redirect(target)
    return redirect(fallback)


def _cart_for(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


@login_required
def cart_detail(request):
    cart = Cart.objects.filter(user=request.user).first()
    items = cart.items.select_related("product", "product__restaurant") if cart else []
    total = sum((item.line_total for item in items), start=0)
    return render(request, "cart_detail.html", {"cart": cart, "items": items, "total": total})


@login_required
@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product.objects.select_related("restaurant"), pk=product_id, is_active=True, category__is_active=True)
    if not product.restaurant_id or product.stock < 1:
        messages.error(request, "Это блюдо сейчас нельзя добавить в корзину.")
        return _return_to(request, "home")
    try:
        quantity = int(request.POST.get("quantity", "1"))
    except (TypeError, ValueError):
        quantity = 0
    if quantity < 1:
        messages.error(request, "Укажите количество от 1.")
        return _return_to(request, "home")

    cart = _cart_for(request.user)
    with transaction.atomic():
        current = list(cart.items.select_related("product").select_for_update())
        existing = next((item for item in current if item.product_id == product.pk), None)
        if any(item.product.restaurant_id != product.restaurant_id for item in current):
            messages.error(request, "В одной корзине могут быть блюда только одного ресторана. Очистите корзину перед сменой ресторана.")
        elif quantity + (existing.quantity if existing else 0) > product.stock:
            messages.error(request, f"Доступно только {product.stock} шт. блюда «{product.name}».")
        elif existing:
            existing.quantity += quantity
            existing.save(update_fields=["quantity"])
            messages.success(request, f"Количество блюда «{product.name}» обновлено.")
        else:
            CartItem.objects.create(cart=cart, product=product, quantity=quantity)
            messages.success(request, f"Блюдо «{product.name}» добавлено в корзину.")
    return _return_to(request, "cart:detail")


@login_required
@require_POST
def update_cart_item(request, item_id):
    cart = get_object_or_404(Cart, user=request.user)
    item = get_object_or_404(CartItem.objects.select_related("product"), cart=cart, pk=item_id)
    try:
        quantity = int(request.POST.get("quantity", "0"))
    except (TypeError, ValueError):
        quantity = 0
    if quantity == 0:
        item.delete()
        messages.success(request, "Блюдо удалено из корзины.")
    elif quantity < 0:
        messages.error(request, "Количество должно быть положительным числом.")
    elif not item.product.is_active or quantity > item.product.stock:
        messages.error(request, f"Доступно только {item.product.stock} шт. блюда «{item.product.name}».")
    else:
        item.quantity = quantity
        item.save(update_fields=["quantity"])
        messages.success(request, "Корзина обновлена.")
    return redirect("cart:detail")


@login_required
@require_POST
def clear_cart(request):
    Cart.objects.filter(user=request.user).delete()
    messages.success(request, "Корзина очищена.")
    return redirect("cart:detail")
