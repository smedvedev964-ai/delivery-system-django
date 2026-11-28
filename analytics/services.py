from django.db.models import Avg, Count, DecimalField, ExpressionWrapper, F, Q, Sum

from delivery.models import Delivery
from orders.models import Order, OrderItem

def order_summary(start_date=None, end_date=None):
    qs = Order.objects.all()
    if start_date: qs = qs.filter(created_at__date__gte=start_date)
    if end_date: qs = qs.filter(created_at__date__lte=end_date)
    return qs.aggregate(
        total_orders=Count("id"),
        delivered_orders=Count("id", filter=Q(status=Order.Status.DELIVERED)),
        cancelled_orders=Count("id", filter=Q(status=Order.Status.CANCELLED)),
        problem_orders=Count("id", filter=Q(status__in=[Order.Status.FAILED, Order.Status.RETURNED])),
        revenue=Sum("total", filter=Q(status=Order.Status.DELIVERED)),
        average_order=Avg("total", filter=Q(status=Order.Status.DELIVERED)),
    )

def popular_products(start_date=None, end_date=None):
    qs = OrderItem.objects.filter(order__status=Order.Status.DELIVERED)
    if start_date: qs = qs.filter(order__created_at__date__gte=start_date)
    if end_date: qs = qs.filter(order__created_at__date__lte=end_date)
    return qs.values("product_name").annotate(quantity=Sum("quantity")).order_by("-quantity")


def popular_categories(start_date=None, end_date=None):
    qs = OrderItem.objects.filter(order__status=Order.Status.DELIVERED)
    if start_date: qs = qs.filter(order__created_at__date__gte=start_date)
    if end_date: qs = qs.filter(order__created_at__date__lte=end_date)
    return qs.values("product__category__name").annotate(
        units_sold=Sum("quantity"),
        revenue=Sum(ExpressionWrapper(
            F("unit_price") * F("quantity"),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )),
    ).order_by("-units_sold")


def courier_workload(start_date=None, end_date=None):
    qs = Delivery.objects.select_related("courier").filter(courier__role="courier")
    if start_date: qs = qs.filter(assigned_at__date__gte=start_date)
    if end_date: qs = qs.filter(assigned_at__date__lte=end_date)
    return qs.values(
        "courier_id", "courier__first_name", "courier__last_name", "courier__username"
    ).annotate(
        assigned=Count("id"),
        active=Count("id", filter=Q(is_current=True)),
        completed=Count("id", filter=Q(completed_at__isnull=False)),
    ).order_by("-assigned")


def average_delivery_time(start_date=None, end_date=None):
    qs = Delivery.objects.select_related("order").filter(completed_at__isnull=False)
    if start_date: qs = qs.filter(order__created_at__date__gte=start_date)
    if end_date: qs = qs.filter(order__created_at__date__lte=end_date)
    durations = [
        (delivery.completed_at - delivery.order.created_at).total_seconds()
        for delivery in qs
    ]
    return sum(durations) / len(durations) if durations else None
