from django.core.paginator import Paginator
from django.db.models import Count, IntegerField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, render

from cart.models import Cart
from .models import Category, Product, Restaurant


def home(request):
    restaurants = Restaurant.objects.filter(is_active=True).annotate(
        available_dishes=Count(
            "products",
            filter=Q(products__is_active=True, products__stock__gt=0),
            distinct=True,
        ),
        sold_quantity=Coalesce(
            Sum("products__orderitem__quantity"),
            Value(0),
            output_field=IntegerField(),
        ),
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
        # Популярность считается по реальному количеству проданных блюд.
        restaurants = restaurants.order_by(
            "-sold_quantity", "-rating_count", "-rating", "name"
        )

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
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            cart_restaurants = set(
                cart.items.values_list("product__restaurant_id", flat=True).distinct()
            )
            if cart_restaurants and cart_restaurants != {restaurant.pk}:
                cart.items.all().delete()

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
    cart_items = []
    cart_quantities = {}
    cart_total = 0
    delivery_fee = 0
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            cart_items = list(cart.items.select_related("product", "product__restaurant"))
            cart_quantities = {item.product_id: item.quantity for item in cart_items}
            cart_total = sum((item.line_total for item in cart_items), start=0)
            if cart_items:
                cart_restaurant = cart_items[0].product.restaurant
                if cart_restaurant.delivery_policy == Restaurant.DeliveryPolicy.FIXED:
                    delivery_fee = cart_restaurant.delivery_fee
                elif cart_restaurant.delivery_policy == Restaurant.DeliveryPolicy.THRESHOLD:
                    threshold = cart_restaurant.free_delivery_threshold
                    if threshold is None or cart_total < threshold:
                        delivery_fee = cart_restaurant.delivery_fee
    products = list(products)
    for product in products:
        product.cart_quantity = cart_quantities.get(product.pk, 0)
    return render(request, "restaurant_detail.html", {
        "restaurant": restaurant,
        "products": products,
        "categories": categories,
        "search_query": query,
        "selected_category": category_id,
        "cart_items": cart_items,
        "cart_total": cart_total,
        "cart_delivery_fee": delivery_fee,
        "cart_grand_total": cart_total + delivery_fee,
        "cart_restaurant": cart_items[0].product.restaurant if cart_items else None,
    })


def product_detail(request, pk):
    product = get_object_or_404(
        Product.objects.select_related("category", "restaurant"),
        pk=pk, is_active=True, category__is_active=True,
    )
    return render(request, "product_detail.html", {"product": product})
