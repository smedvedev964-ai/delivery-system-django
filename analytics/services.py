from django.db.models import Count, Sum, Avg
from orders.models import Order, OrderItem

def order_summary(start_date=None, end_date=None):
    qs = Order.objects.all()
    if start_date: qs = qs.filter(created_at__date__gte=start_date)
    if end_date: qs = qs.filter(created_at__date__lte=end_date)
    return qs.aggregate(total_orders=Count("id"), revenue=Sum("total"), average_order=Avg("total"))

def popular_products(start_date=None, end_date=None):
    qs = OrderItem.objects.filter(order__status=Order.Status.DELIVERED)
    if start_date: qs = qs.filter(order__created_at__date__gte=start_date)
    if end_date: qs = qs.filter(order__created_at__date__lte=end_date)
    return qs.values("product_name").annotate(quantity=Sum("quantity")).order_by("-quantity")
