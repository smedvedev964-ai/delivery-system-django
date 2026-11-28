from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from catalog import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("restaurant/<slug:slug>/", views.restaurant_detail, name="restaurant_detail"),
    path("product/<int:pk>/", views.product_detail, name="product_detail"),
    path("cart/", include("cart.urls")),
    path("orders/", include("orders.urls")),
    path("delivery/", include("delivery.urls")),
    path("notifications/", include("notifications.urls")),
    path("analytics/", include("analytics.urls")),
    path("accounts/", include("accounts.urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
