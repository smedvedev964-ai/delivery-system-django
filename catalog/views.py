from django.db.models import Q
from django.shortcuts import render

from .models import Category, Product


def home(request):
    products = Product.objects.filter(
        is_active=True,
        category__is_active=True,
        stock__gt=0,
    ).select_related("category")
    categories = Category.objects.filter(is_active=True)

    query = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "").strip()

    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
    if category_id.isdigit():
        products = products.filter(category_id=int(category_id))

    return render(request, "home.html", {
        "products": products[:24],
        "categories": categories,
        "search_query": query,
        "selected_category": category_id,
    })
