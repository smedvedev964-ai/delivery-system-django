from django.db import transaction
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from accounts.models import User
from orders.models import Order
from .models import CourierProfile, Delivery

@transaction.atomic
def assign_courier(*, order, courier, manager):
    if getattr(manager, "role", "") not in {"manager", "admin"}:
        raise ValidationError("Назначать курьеров может только менеджер или администратор.")
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.status != Order.Status.PREPARING:
        raise ValidationError("Назначить курьера можно только для подготовленного заказа.")
    profile = CourierProfile.objects.select_for_update().filter(user=courier, is_available=True).first()
    if not profile or not courier.is_active or courier.role != User.Role.COURIER:
        raise ValidationError("Курьер неактивен или недоступен.")
    active = Delivery.objects.filter(courier=courier, is_current=True, order__status__in=[Order.Status.COURIER_ASSIGNED, Order.Status.HANDED_TO_COURIER, Order.Status.IN_TRANSIT]).count()
    if active >= profile.max_active_deliveries:
        raise ValidationError("Курьер достиг лимита активных доставок.")
    Delivery.objects.filter(order=order, is_current=True).update(is_current=False)
    delivery = Delivery.objects.create(order=order, courier=courier, assigned_by=manager)
    order.status = Order.Status.COURIER_ASSIGNED
    order.save(update_fields=["status", "updated_at"])
    from orders.models import OrderStatusHistory
    OrderStatusHistory.objects.create(order=order, actor=manager, old_status=Order.Status.PREPARING,
                                      new_status=Order.Status.COURIER_ASSIGNED, comment="Курьер назначен")
    return delivery
