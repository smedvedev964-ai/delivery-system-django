from .models import CartItem


def cart_indicator(request):
    has_items = False
    if request.user.is_authenticated:
        has_items = CartItem.objects.filter(cart__user=request.user).exists()
    return {"cart_has_items": has_items}
