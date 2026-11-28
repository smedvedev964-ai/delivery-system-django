from .models import Address


def saved_delivery_address(request):
    address = None
    if request.user.is_authenticated:
        address = Address.objects.filter(user=request.user).first()
    return {"saved_delivery_address": address}
