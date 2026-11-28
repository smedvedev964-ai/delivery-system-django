import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from accounts.forms import AddressStepForm
from accounts.models import Address
from accounts.models import User
from cart.models import Cart
from catalog.models import Restaurant
from delivery.models import CourierProfile
from .forms import ReviewForm
from .models import Order, Review
from .services import TRANSITIONS, change_order_status, create_order


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
    saved_address = Address.objects.filter(user=request.user).first()
    address_form = AddressStepForm(request.POST or None, instance=saved_address)
    context = {
        "items": items,
        "saved_address": saved_address,
        "address_form": address_form,
        "checkout_key": request.session.get("checkout_key"),
    }
    if request.method == "POST":
        if not address_form.is_valid():
            context["error"] = "Проверьте адрес доставки: укажите город, улицу и дом."
            return render(request, "checkout.html", context, status=400)

        try:
            with transaction.atomic():
                address = address_form.save(commit=False)
                address.user = request.user
                address.is_default = True
                address.save()
                order, _ = create_order(
                    user=request.user,
                    address=address,
                    comment=request.POST.get("order_comment", "").strip(),
                    idempotency_key=request.POST.get("idempotency_key") or None,
                )
        except ValidationError as exc:
            context["error"] = " ".join(exc.messages)
            return render(request, "checkout.html", context, status=400)

        request.session["checkout_key"] = uuid.uuid4().hex
        return redirect("orders:success", order_id=order.pk)

    return render(request, "checkout.html", context)


@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, pk=order_id, customer=request.user)
    return render(request, "order_success.html", {"order": order})


@role_required("client")
def order_history(request):
    orders = (
        Order.objects.filter(customer=request.user)
        .select_related("address")
        .prefetch_related("items", "items__product__restaurant")
    )
    return render(request, "orders/history.html", {"orders": orders})


@role_required("client")
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.filter(customer=request.user)
        .select_related("address")
        .prefetch_related("items__product__restaurant", "status_history__actor"),
        pk=order_id,
    )
    review = Review.objects.filter(order=order, customer=request.user).first()
    review_form = ReviewForm(request.POST or None)

    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "cancel":
                change_order_status(
                    order=order,
                    actor=request.user,
                    new_status=Order.Status.CANCELLED,
                    comment="Клиент отменил заказ",
                )
                messages.success(request, "Заказ отменён. Остатки блюд возвращены в меню.")
                return redirect("orders:detail", order_id=order.pk)
            if action == "review":
                if order.status != Order.Status.DELIVERED:
                    raise ValidationError("Оставить отзыв можно после доставки заказа.")
                if review:
                    raise ValidationError("Для этого заказа отзыв уже оставлен.")
                if review_form.is_valid():
                    review = review_form.save(commit=False)
                    review.customer = request.user
                    review.order = order
                    review.save()
                    restaurant_id = order.items.values_list(
                        "product__restaurant_id", flat=True
                    ).first()
                    if restaurant_id:
                        rating = Review.objects.filter(
                            order__items__product__restaurant_id=restaurant_id
                        ).values("order_id", "rating").distinct().aggregate(
                            average=Avg("rating"), count=Count("order_id")
                        )
                        Restaurant.objects.filter(pk=restaurant_id).update(
                            rating=rating["average"], rating_count=rating["count"]
                        )
                    messages.success(request, "Спасибо за отзыв!")
                    return redirect("orders:detail", order_id=order.pk)
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, " ".join(getattr(exc, "messages", [str(exc)])))
        if action == "review" and not review_form.is_valid():
            messages.error(request, "Проверьте оценку и текст отзыва.")

    return render(request, "orders/detail.html", {
        "order": order,
        "review": review,
        "review_form": review_form,
        "can_cancel": order.status in {Order.Status.PENDING, Order.Status.CONFIRMED},
    })


@role_required("manager", "admin")
def manager_dashboard(request):
    if request.method == "POST":
        order = get_object_or_404(Order, pk=request.POST.get("order_id"))
        try:
            if request.POST.get("action") == "assign":
                from delivery.services import assign_courier

                courier = get_object_or_404(
                    User, pk=request.POST.get("courier_id"), role=User.Role.COURIER
                )
                assign_courier(order=order, courier=courier, manager=request.user)
                messages.success(request, f"Курьер назначен на заказ {order.number}.")
            elif request.POST.get("action") == "status":
                change_order_status(
                    order=order,
                    actor=request.user,
                    new_status=request.POST.get("status", ""),
                    comment=request.POST.get("comment", "").strip(),
                )
                messages.success(request, f"Статус заказа {order.number} обновлён.")
            else:
                raise ValidationError("Неизвестное действие.")
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, " ".join(getattr(exc, "messages", [str(exc)])))
        return redirect("orders:manager")

    status_filter = request.GET.get("status", "").strip()
    orders = Order.objects.select_related("customer").prefetch_related(
        "items__product", "deliveries__courier", "status_history"
    )
    if status_filter in dict(Order.Status.choices):
        orders = orders.filter(status=status_filter)
    couriers = list(
        CourierProfile.objects.filter(user__role=User.Role.COURIER, user__is_active=True, is_available=True)
        .select_related("user").order_by("user__first_name", "user__username")
    )
    available_statuses = {}
    for order in orders:
        available_statuses[order.pk] = [
            (value, dict(Order.Status.choices).get(value, value))
            for value in TRANSITIONS.get(order.status, set())
            if value != Order.Status.COURIER_ASSIGNED
        ]
        order.allowed_statuses = available_statuses[order.pk]
        order.can_assign_courier = order.status in {
            Order.Status.PREPARING, Order.Status.COURIER_ASSIGNED
        }
    return render(request, "orders/manager_dashboard.html", {
        "orders": orders,
        "couriers": couriers,
        "available_statuses": available_statuses,
        "status_choices": Order.Status.choices,
        "selected_status": status_filter,
    })
