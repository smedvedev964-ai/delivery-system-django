from django.urls import path

from . import views

app_name = "orders"
urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("<int:order_id>/success/", views.order_success, name="success"),
]
