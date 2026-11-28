from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from orders.models import Order
from orders.services import TRANSITIONS, change_order_status
from .models import Delivery


@role_required("courier")
def courier_dashboard(request):
    if request.method == "POST":
        delivery = get_object_or_404(
            Delivery.objects.select_related("order"),
            order_id=request.POST.get("order_id"),
            courier=request.user,
            is_current=True,
        )
        try:
            change_order_status(
                order=delivery.order,
                actor=request.user,
                new_status=request.POST.get("status", ""),
                comment=request.POST.get("comment", "").strip(),
            )
            messages.success(request, "Статус доставки обновлён.")
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, " ".join(getattr(exc, "messages", [str(exc)])))
        return redirect("delivery:courier")

    deliveries = (
        Delivery.objects.filter(courier=request.user)
        .select_related("order", "order__customer")
        .prefetch_related("order__items", "order__status_history")
    )
    active_deliveries = deliveries.filter(is_current=True)
    completed_deliveries = deliveries.filter(is_current=False)
    allowed_statuses = {
        order.pk: [
            (status, dict(Order.Status.choices).get(status, status))
            for status in TRANSITIONS.get(order.status, set())
            if status in {
                Order.Status.HANDED_TO_COURIER,
                Order.Status.IN_TRANSIT,
                Order.Status.DELIVERED,
                Order.Status.FAILED,
            }
        ]
        for order in (delivery.order for delivery in active_deliveries)
    }
    for delivery in active_deliveries:
        delivery.allowed_statuses = allowed_statuses.get(delivery.order_id, [])
    return render(request, "delivery/courier_dashboard.html", {
        "active_deliveries": active_deliveries,
        "completed_deliveries": completed_deliveries,
        "allowed_statuses": allowed_statuses,
    })
