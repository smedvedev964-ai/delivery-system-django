from django.db import transaction
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from accounts.models import User
from notifications.models import Notification
from orders.models import Order
from .models import CourierProfile, Delivery

@transaction.atomic
def assign_courier(*, order, courier, manager):
    if getattr(manager, "role", "") not in {"manager", "admin"} and not manager.is_superuser:
        raise ValidationError("Назначать курьеров может только менеджер или администратор.")
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.status not in {Order.Status.PREPARING, Order.Status.COURIER_ASSIGNED}:
        raise ValidationError("Назначить курьера можно только для подготовленного заказа.")
    profile = CourierProfile.objects.select_for_update().filter(user=courier, is_available=True).first()
    if not profile or not courier.is_active or courier.role != User.Role.COURIER:
        raise ValidationError("Курьер неактивен или недоступен.")
    current_assignment = Delivery.objects.filter(
        order=order, is_current=True, courier=courier
    ).first()
    if current_assignment:
        return current_assignment
    active = Delivery.objects.filter(
        courier=courier,
        is_current=True,
        order__status__in=[
            Order.Status.COURIER_ASSIGNED,
            Order.Status.HANDED_TO_COURIER,
            Order.Status.IN_TRANSIT,
        ],
    ).exclude(order=order).count()
    if active >= profile.max_active_deliveries:
        raise ValidationError("Курьер достиг лимита активных доставок.")
    was_assigned = order.status == Order.Status.COURIER_ASSIGNED
    Delivery.objects.filter(order=order, is_current=True).update(is_current=False)
    delivery = Delivery.objects.create(order=order, courier=courier, assigned_by=manager)
    old_status = order.status
    order.status = Order.Status.COURIER_ASSIGNED
    order.save(update_fields=["status", "updated_at"])
    from orders.models import OrderStatusHistory
    OrderStatusHistory.objects.create(
        order=order,
        actor=manager,
        old_status=old_status,
        new_status=Order.Status.COURIER_ASSIGNED,
        comment="Курьер переназначен" if was_assigned else "Курьер назначен",
    )
    Notification.objects.create(
        user=order.customer,
        title="Курьер назначен",
        message=f"На заказ № {order.number} назначен курьер.",
    )
    Notification.objects.create(
        user=courier,
        title="Новая доставка",
        message=f"Вам назначен заказ № {order.number}.",
    )
    return delivery
