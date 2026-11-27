from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied
from django.db.models import F
from .models import Order, OrderItem, OrderStatusHistory
from cart.models import Cart
from notifications.models import Notification

# Допустимые переходы и роли-инициаторы. Политика отмены клиента: до подтверждения.
TRANSITIONS = {
    Order.Status.PENDING: {Order.Status.CONFIRMED, Order.Status.CANCELLED},
    Order.Status.CONFIRMED: {Order.Status.PREPARING, Order.Status.CANCELLED},
    Order.Status.PREPARING: {Order.Status.COURIER_ASSIGNED, Order.Status.CANCELLED},
    Order.Status.COURIER_ASSIGNED: {Order.Status.HANDED_TO_COURIER, Order.Status.PREPARING},
    Order.Status.HANDED_TO_COURIER: {Order.Status.IN_TRANSIT},
    Order.Status.IN_TRANSIT: {Order.Status.DELIVERED, Order.Status.FAILED},
    Order.Status.FAILED: {Order.Status.RETURNED, Order.Status.IN_TRANSIT},
}

def _address_snapshot(address):
    return {"city": address.city, "street": address.street, "house": address.house,
            "apartment": address.apartment, "comment": address.comment}

@transaction.atomic
def create_order(*, user, address, comment="", idempotency_key=None, delivery_fee=Decimal("0.00")):
    if idempotency_key:
        existing = Order.objects.filter(idempotency_key=idempotency_key).first()
        if existing: return existing, False
    cart = Cart.objects.select_for_update().filter(user=user).first()
    if address.user_id != user.pk: raise PermissionDenied("Нельзя оформить заказ на чужой адрес.")
    if not cart: raise ValidationError("Корзина пуста.")
    items = list(cart.items.select_related("product").select_for_update())
    if not items: raise ValidationError("Нельзя оформить пустую корзину.")
    total = Decimal("0.00")
    for item in items:
        product = item.product
        if not product.is_active: raise ValidationError(f"Товар «{product.name}» больше недоступен.")
        if item.quantity > product.stock: raise ValidationError(f"Недостаточный остаток товара «{product.name}»: доступно {product.stock}.")
        total += product.price * item.quantity
    order = Order.objects.create(customer=user, address=address, address_snapshot=_address_snapshot(address),
        items_total=total, delivery_fee=delivery_fee, total=total + delivery_fee, comment=comment,
        idempotency_key=idempotency_key)
    for item in items:
        product = item.product
        updated = type(product).objects.filter(pk=product.pk, stock__gte=item.quantity).update(stock=F("stock")-item.quantity)
        if not updated: raise ValidationError(f"Остаток товара «{product.name}» изменился. Обновите корзину.")
        OrderItem.objects.create(order=order, product=product, product_name=product.name,
                                 quantity=item.quantity, unit_price=product.price)
    OrderStatusHistory.objects.create(order=order, actor=user, old_status="", new_status=Order.Status.PENDING,
                                      comment="Заказ создан")
    Notification.objects.create(user=user, title="Заказ создан", message=f"Заказ № {order.number} успешно создан.")
    cart.items.all().delete()
    return order, True

@transaction.atomic
def change_order_status(*, order, actor, new_status, comment=""):
    order = Order.objects.select_for_update().get(pk=order.pk)
    if new_status not in TRANSITIONS.get(order.status, set()):
        raise ValidationError("Недопустимый переход статуса заказа.")
    role = getattr(actor, "role", "")
    if role == "client":
        if actor.pk != order.customer_id or new_status != Order.Status.CANCELLED or order.status not in {Order.Status.PENDING, Order.Status.CONFIRMED}:
            raise PermissionDenied("Недостаточно прав для этого действия.")
    elif role == "courier":
        if new_status not in {Order.Status.IN_TRANSIT, Order.Status.DELIVERED, Order.Status.FAILED}:
            raise PermissionDenied("Курьер не может выполнить этот переход.")
        if not order.deliveries.filter(courier=actor, is_current=True).exists():
            raise PermissionDenied("Заказ не назначен этому курьеру.")
    elif role not in {"manager", "admin"}:
        raise PermissionDenied("Недостаточно прав.")
    old = order.status
    order.status = new_status
    order.save(update_fields=["status", "updated_at"])
    OrderStatusHistory.objects.create(order=order, actor=actor, old_status=old, new_status=new_status, comment=comment)
    Notification.objects.create(user=order.customer, title="Статус заказа изменён", message=f"Заказ № {order.number}: {order.get_status_display()}.")
    return order
