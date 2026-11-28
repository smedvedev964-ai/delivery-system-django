import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import Address
from cart.models import Cart
from .models import Order
from .services import create_order


@login_required
def checkout(request):
    if getattr(request.user, "role", "") != "client":
        raise PermissionDenied("Оформлять заказы может только клиент.")
    cart = Cart.objects.filter(user=request.user).first()
    items = cart.items.select_related("product", "product__restaurant") if cart else []
    if not items:
        messages.info(request, "Добавьте блюда в корзину перед оформлением заказа.")
        return redirect("cart:detail")
    if not request.user.first_name:
        messages.info(request, "Укажите имя, чтобы курьер знал, кому передать заказ.")
        return redirect("accounts:onboarding_step", step="name")
    if not request.user.phone:
        messages.info(request, "Укажите номер телефона для связи по доставке.")
        return redirect("accounts:onboarding_step", step="phone")

    if request.method == "GET":
        request.session.setdefault("checkout_key", uuid.uuid4().hex)
    addresses = Address.objects.filter(user=request.user)
    context = {"items": items, "addresses": addresses, "checkout_key": request.session.get("checkout_key")}
    if request.method == "POST":
        address = None
        address_id = request.POST.get("address_id", "").strip()
        if address_id:
            address = get_object_or_404(addresses, pk=address_id)
        else:
            fields = {key: request.POST.get(key, "").strip() for key in ("city", "street", "house", "apartment", "comment")}
            if not all(fields[key] for key in ("city", "street", "house")):
                context["error"] = "Заполните город, улицу и дом или выберите сохранённый адрес."
                return render(request, "checkout.html", context, status=400)

        try:
            with transaction.atomic():
                if address is None:
                    address = Address.objects.create(user=request.user, **fields)
                order, _ = create_order(
                    user=request.user,
                    address=address,
                    comment=request.POST.get("order_comment", "").strip(),
                    idempotency_key=request.POST.get("idempotency_key") or None,
                )
        except ValidationError as exc:
            context["error"] = " ".join(exc.messages)
            context["addresses"] = Address.objects.filter(user=request.user)
            return render(request, "checkout.html", context, status=400)

        request.session["checkout_key"] = uuid.uuid4().hex
        return redirect("orders:success", order_id=order.pk)

    return render(request, "checkout.html", context)


@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, pk=order_id, customer=request.user)
    return render(request, "order_success.html", {"order": order})
