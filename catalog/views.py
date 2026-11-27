from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404, render

from .models import Category, Product, Restaurant


def home(request):
    restaurants = Restaurant.objects.filter(is_active=True).annotate(
        available_dishes=Count(
            "products",
            filter=Q(products__is_active=True, products__stock__gt=0),
            distinct=True,
        )
    )
    query = request.GET.get("q", "").strip()
    cuisine = request.GET.get("cuisine", "").strip()
    sort = request.GET.get("sort", "popular").strip()

    if query:
        restaurants = restaurants.filter(
            Q(name__icontains=query) | Q(cuisine__icontains=query)
            | Q(description__icontains=query)
        )
    if cuisine and cuisine != "Все":
        restaurants = restaurants.filter(cuisine=cuisine)

    if sort == "rating":
        restaurants = restaurants.order_by("-rating", "name")
    elif sort == "delivery":
        restaurants = restaurants.order_by("delivery_min", "name")
    else:
        restaurants = restaurants.order_by("-rating", "name")

    cuisines = list(
        Restaurant.objects.filter(is_active=True)
        .order_by("cuisine").values_list("cuisine", flat=True).distinct()
    )
    page_obj = Paginator(restaurants, 12).get_page(request.GET.get("page"))
    return render(request, "home.html", {
        "restaurants": page_obj.object_list,
        "page_obj": page_obj,
        "cuisines": cuisines,
        "search_query": query,
        "selected_cuisine": cuisine,
        "selected_sort": sort,
        "total_restaurants": restaurants.count(),
    })


def restaurant_detail(request, slug):
    restaurant = get_object_or_404(Restaurant, slug=slug, is_active=True)
    products = restaurant.products.filter(
        is_active=True, stock__gt=0
    ).select_related("category")
    query = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "").strip()
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    if category_id.isdigit():
        products = products.filter(category_id=int(category_id))
    categories = Category.objects.filter(
        is_active=True, products__restaurant=restaurant,
        products__is_active=True, products__stock__gt=0
    ).distinct().order_by("name")
    return render(request, "restaurant_detail.html", {
        "restaurant": restaurant,
        "products": products,
        "categories": categories,
        "search_query": query,
        "selected_category": category_id,
    })


def product_detail(request, pk):
    product = get_object_or_404(
        Product.objects.select_related("category", "restaurant"),
        pk=pk, is_active=True, category__is_active=True,
    )
    return render(request, "product_detail.html", {"product": product})
