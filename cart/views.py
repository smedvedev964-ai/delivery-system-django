from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
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


def _is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def _cart_login_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if _is_ajax(request):
                from django.urls import reverse
                return JsonResponse({
                    "error": "Сессия завершилась. Войдите в аккаунт, чтобы продолжить.",
                    "login_url": f"{reverse('accounts:login')}?next={request.path}",
                }, status=401)
            return redirect_to_login(request.get_full_path())
        return view(request, *args, **kwargs)
    return wrapped


def _sidebar_payload(request, product):
    cart = Cart.objects.filter(user=request.user).first()
    items = list(cart.items.select_related("product", "product__restaurant") if cart else [])
    subtotal = sum((item.line_total for item in items), start=0)
    restaurant = items[0].product.restaurant if items else product.restaurant
    delivery_fee = 0
    if items:
        from orders.services import calculate_delivery_fee
        delivery_fee = calculate_delivery_fee(restaurant=restaurant, subtotal=subtotal)
    context = {
        "cart_items": items,
        "cart_total": subtotal,
        "cart_delivery_fee": delivery_fee,
        "cart_grand_total": subtotal + delivery_fee,
        "restaurant": restaurant,
        "request": request,
        "user": request.user,
    }
    return {
        "sidebar_html": render_to_string("cart_sidebar.html", context, request=request),
        "cart_has_items": bool(items),
        "quantity": next((item.quantity for item in items if item.product_id == product.pk), 0),
    }


@_cart_login_required
def cart_detail(request):
    cart = Cart.objects.filter(user=request.user).first()
    items = cart.items.select_related("product", "product__restaurant") if cart else []
    total = sum((item.line_total for item in items), start=0)
    return render(request, "cart_detail.html", {"cart": cart, "items": items, "total": total})


@_cart_login_required
@require_POST
def add_to_cart(request, product_id):
    is_ajax = _is_ajax(request)
    action = request.POST.get("action", "increment")
    cart = _cart_for(request.user)
    error = None
    product = None
    with transaction.atomic():
        cart = Cart.objects.select_for_update().get(pk=cart.pk, user=request.user)
        product = (
            Product.objects.select_related("category")
            .select_for_update(of=("self",))
            .filter(pk=product_id, is_active=True, category__is_active=True, restaurant__is_active=True)
            .first()
        )
        if not product or not product.restaurant_id or (product.stock < 1 and action != "decrement"):
            error = "Это блюдо сейчас нельзя добавить в корзину."
        current = list(cart.items.select_for_update(of=("self",)).order_by("pk"))
        existing = next(
            (item for item in current if product and item.product_id == product.pk), None
        )
        current_restaurants = set(
            Product.objects.filter(pk__in=[item.product_id for item in current])
            .values_list("restaurant_id", flat=True)
        )
        if not error and current_restaurants and current_restaurants != {product.restaurant_id}:
            cart.items.all().delete()
            current = []
            existing = None
        current_quantity = existing.quantity if existing else 0
        if error:
            pass
        elif action == "decrement":
            if existing and current_quantity > 1:
                existing.quantity -= 1
                existing.save(update_fields=["quantity"])
            elif existing:
                existing.delete()
        elif action == "increment":
            if current_quantity >= product.stock:
                error = f"Доступно только {product.stock} шт. блюда «{product.name}»."
            elif existing:
                existing.quantity += 1
                existing.save(update_fields=["quantity"])
            else:
                CartItem.objects.create(cart=cart, product=product, quantity=1)
        else:
            error = "Не удалось изменить количество блюда."
    if error:
        if is_ajax:
            return JsonResponse({"error": error}, status=400)
        messages.error(request, error)
        return _return_to(request, "home")
    if is_ajax:
        payload = _sidebar_payload(request, product)
        payload["product_id"] = product.pk
        return JsonResponse(payload)
    return _return_to(request, "cart:detail")


@_cart_login_required
@require_POST
def update_cart_item(request, item_id):
    action = request.POST.get("action")
    cart_id = get_object_or_404(Cart, user=request.user).pk
    error = None
    removed = False
    with transaction.atomic():
        cart = Cart.objects.select_for_update().get(pk=cart_id, user=request.user)
        item_ref = get_object_or_404(CartItem, cart=cart, pk=item_id)
        product = Product.objects.select_for_update(of=("self",)).get(pk=item_ref.product_id)
        item = get_object_or_404(
            CartItem.objects.select_for_update(of=("self",)), cart=cart, pk=item_id
        )
        if action == "increment":
            quantity = item.quantity + 1
        elif action == "decrement":
            quantity = item.quantity - 1
        else:
            quantity_raw = request.POST.get("quantity")
            try:
                quantity = int(quantity_raw) if quantity_raw is not None else None
            except (TypeError, ValueError):
                quantity = None
        if quantity is None:
            error = "Укажите корректное количество блюда."
        elif quantity == 0:
            item.delete()
            removed = True
        elif quantity < 0:
            error = "Количество должно быть положительным числом."
        elif action != "decrement" and (
            not product.is_active
            or not product.category.is_active
            or (product.restaurant_id and not product.restaurant.is_active)
            or quantity > product.stock
        ):
            error = f"Доступно только {product.stock} шт. блюда «{product.name}»."
        else:
            item.quantity = quantity
            item.save(update_fields=["quantity"])
    if removed and not _is_ajax(request):
        messages.success(request, "Блюдо удалено из корзины.")
    elif not error and not _is_ajax(request):
        messages.success(request, "Корзина обновлена.")
    if _is_ajax(request):
        if error:
            return JsonResponse({"error": error}, status=400)
        cart = Cart.objects.filter(user=request.user).first()
        items = list(cart.items.select_related("product", "product__restaurant") if cart else [])
        total = sum((cart_item.line_total for cart_item in items), start=0)
        context = {"cart": cart, "items": items, "total": total, "request": request}
        return JsonResponse({
            "cart_html": render_to_string("cart_detail_content.html", context, request=request),
            "cart_has_items": bool(items),
        })
    if error:
        messages.error(request, error)
    return redirect("cart:detail")


@login_required
@require_POST
def clear_cart(request):
    with transaction.atomic():
        cart = Cart.objects.select_for_update().filter(user=request.user).first()
        if cart:
            cart.items.all().delete()
    messages.success(request, "Корзина очищена.")
    return redirect("cart:detail")
