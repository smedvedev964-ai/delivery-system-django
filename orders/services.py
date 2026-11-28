from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import F

from cart.models import Cart
from catalog.models import Product
from notifications.models import Notification
from .models import Order, OrderItem, OrderStatusHistory


# Допустимые переходы между статусами заказа.
TRANSITIONS = {
    Order.Status.PENDING: {
        Order.Status.CONFIRMED,
        Order.Status.CANCELLED,
    },
    Order.Status.CONFIRMED: {
        Order.Status.PREPARING,
        Order.Status.CANCELLED,
    },
    Order.Status.PREPARING: {
        Order.Status.COURIER_ASSIGNED,
    },
    Order.Status.COURIER_ASSIGNED: {
        Order.Status.HANDED_TO_COURIER,
    },
    Order.Status.HANDED_TO_COURIER: {
        Order.Status.IN_TRANSIT,
    },
    Order.Status.IN_TRANSIT: {
        Order.Status.DELIVERED,
        Order.Status.FAILED,
    },
    Order.Status.FAILED: {
        Order.Status.RETURNED,
        Order.Status.IN_TRANSIT,
    },
}


def _address_snapshot(address):
    return {
        "city": address.city,
        "street": address.street,
        "house": address.house,
        "apartment": address.apartment,
        "comment": address.comment,
    }


def calculate_delivery_fee(*, restaurant, subtotal):
    """Рассчитывает стоимость доставки по тарифу выбранного ресторана."""
    if restaurant.delivery_policy == "free":
        return Decimal("0.00")

    if (
        restaurant.delivery_policy == "threshold"
        and restaurant.free_delivery_threshold is not None
        and subtotal >= restaurant.free_delivery_threshold
    ):
        return Decimal("0.00")

    return restaurant.delivery_fee


def _existing_idempotent_order(*, user, idempotency_key):
    if not idempotency_key:
        return None
    existing_order = Order.objects.filter(idempotency_key=idempotency_key).first()
    if existing_order and existing_order.customer_id != user.pk:
        raise PermissionDenied("Ключ запроса уже использован другим аккаунтом.")
    return existing_order


@transaction.atomic
def create_order(*, user, address, comment="", idempotency_key=None):
    if idempotency_key:
        if len(idempotency_key) > 64:
            raise ValidationError("Ключ оформления заказа слишком длинный.")
        existing_order = _existing_idempotent_order(user=user, idempotency_key=idempotency_key)
        if existing_order:
            return existing_order, False

    if address.user_id != user.pk:
        raise PermissionDenied("Нельзя оформить заказ на чужой адрес.")

    cart = Cart.objects.select_for_update().filter(user=user).first()
    if cart is None:
        raise ValidationError("Корзина пуста.")

    # A duplicate submission may have waited for this cart lock while the first
    # request finished. Recheck the key after acquiring the lock before reading items.
    existing_order = _existing_idempotent_order(user=user, idempotency_key=idempotency_key)
    if existing_order:
        return existing_order, False

    product_ids = list(
        cart.items.order_by("product_id").values_list("product_id", flat=True).distinct()
    )
    if not product_ids:
        raise ValidationError("Нельзя оформить пустую корзину.")

    # Lock product rows separately. Locking the joined nullable restaurant relation
    # makes PostgreSQL reject FOR UPDATE on the outer-joined table.
    list(
        Product.objects.select_for_update(of=("self",))
        .filter(pk__in=product_ids)
        .order_by("pk")
    )
    items = list(
        cart.items.select_related("product", "product__restaurant", "product__category").order_by("pk")
    )
    if not items:
        raise ValidationError("Нельзя оформить пустую корзину.")

    restaurant_ids = {item.product.restaurant_id for item in items}
    if len(restaurant_ids) != 1 or None in restaurant_ids:
        raise ValidationError(
            "В одном заказе могут быть блюда только одного ресторана."
        )

    restaurant = items[0].product.restaurant
    if not restaurant.is_active:
        raise ValidationError("Этот ресторан временно не принимает заказы.")
    items_total = Decimal("0.00")

    for item in items:
        product = item.product

        if not product.is_active or not product.category.is_active:
            raise ValidationError(
                f"Блюдо «{product.name}» больше недоступно."
            )

        if item.quantity > product.stock:
            raise ValidationError(
                f"Недостаточный остаток блюда «{product.name}»: "
                f"доступно {product.stock}."
            )

        items_total += product.price * item.quantity

    delivery_fee = calculate_delivery_fee(
        restaurant=restaurant,
        subtotal=items_total,
    )

    order = Order.objects.create(
        customer=user,
        address=address,
        address_snapshot=_address_snapshot(address),
        items_total=items_total,
        delivery_fee=delivery_fee,
        total=items_total + delivery_fee,
        comment=comment,
        idempotency_key=idempotency_key,
    )

    for item in items:
        product = item.product
        updated_rows = type(product).objects.filter(
            pk=product.pk,
            stock__gte=item.quantity,
        ).update(stock=F("stock") - item.quantity)

        if not updated_rows:
            raise ValidationError(
                f"Остаток блюда «{product.name}» изменился. "
                "Обновите корзину."
            )

        OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            quantity=item.quantity,
            unit_price=product.price,
        )

    OrderStatusHistory.objects.create(
        order=order,
        actor=user,
        old_status="",
        new_status=Order.Status.PENDING,
        comment="Заказ создан",
    )
    Notification.objects.create(
        user=user,
        title="Заказ создан",
        message=f"Заказ № {order.number} успешно создан.",
    )

    cart.items.all().delete()
    return order, True


@transaction.atomic
def change_order_status(*, order, actor, new_status, comment=""):
    order = Order.objects.select_for_update().get(pk=order.pk)

    if new_status not in TRANSITIONS.get(order.status, set()):
        raise ValidationError("Недопустимый переход статуса заказа.")

    role = "admin" if actor.is_superuser else getattr(actor, "role", "")

    if new_status == Order.Status.COURIER_ASSIGNED:
        raise ValidationError("Назначайте курьера через действие назначения доставки.")

    if role == "client":
        can_cancel = (
            actor.pk == order.customer_id
            and new_status == Order.Status.CANCELLED
            and order.status in {
                Order.Status.PENDING,
                Order.Status.CONFIRMED,
            }
        )
        if not can_cancel:
            raise PermissionDenied(
                "Недостаточно прав для этого действия."
            )

    elif role == "courier":
        courier_statuses = {
            Order.Status.HANDED_TO_COURIER,
            Order.Status.IN_TRANSIT,
            Order.Status.DELIVERED,
            Order.Status.FAILED,
        }
        if new_status not in courier_statuses:
            raise PermissionDenied(
                "Курьер не может выполнить этот переход."
            )

        is_assigned = order.deliveries.filter(
            courier=actor,
            is_current=True,
        ).exists()
        if not is_assigned:
            raise PermissionDenied("Заказ не назначен этому курьеру.")

    elif role not in {"manager", "admin"}:
        raise PermissionDenied("Недостаточно прав.")

    old_status = order.status
    order.status = new_status
    order.save(update_fields=["status", "updated_at"])

    if new_status == Order.Status.CANCELLED and old_status in {
        Order.Status.PENDING,
        Order.Status.CONFIRMED,
    }:
        for item in order.items.select_related("product"):
            Product.objects.filter(pk=item.product_id).update(
                stock=F("stock") + item.quantity
            )

    if new_status in {Order.Status.DELIVERED, Order.Status.RETURNED}:
        from django.utils import timezone

        order.deliveries.filter(is_current=True).update(
            is_current=False,
            completed_at=timezone.now() if new_status == Order.Status.DELIVERED else None,
        )

    OrderStatusHistory.objects.create(
        order=order,
        actor=actor,
        old_status=old_status,
        new_status=new_status,
        comment=comment,
    )
    Notification.objects.create(
        user=order.customer,
        title="Статус заказа изменён",
        message=(
            f"Заказ № {order.number}: "
            f"{order.get_status_display()}."
        ),
    )

    return order
