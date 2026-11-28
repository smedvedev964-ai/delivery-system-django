from datetime import timedelta

from django.shortcuts import render
from django.utils import timezone

from accounts.decorators import role_required
from .forms import AnalyticsDateFilterForm
from .services import (
    average_delivery_time,
    courier_workload,
    order_summary,
    popular_categories,
    popular_products,
)


@role_required("manager", "admin")
def dashboard(request):
    form = AnalyticsDateFilterForm(request.GET or None)
    today = timezone.localdate()
    start_date = today - timedelta(days=29)
    end_date = today
    if form.is_valid():
        start_date = form.cleaned_data.get("start_date") or start_date
        end_date = form.cleaned_data.get("end_date") or end_date
    average_seconds = average_delivery_time(start_date, end_date)
    return render(request, "analytics/dashboard.html", {
        "form": form,
        "start_date": start_date,
        "end_date": end_date,
        "summary": order_summary(start_date, end_date),
        "popular_products": popular_products(start_date, end_date)[:10],
        "popular_categories": popular_categories(start_date, end_date)[:10],
        "courier_workload": courier_workload(start_date, end_date),
        "average_delivery_minutes": average_seconds / 60 if average_seconds is not None else None,
    })
