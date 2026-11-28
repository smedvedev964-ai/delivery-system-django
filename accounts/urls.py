from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from .forms import EmailOrUsernameAuthenticationForm
from . import views

app_name = "accounts"
urlpatterns = [
    path("login/", LoginView.as_view(template_name="accounts/login.html", authentication_form=EmailOrUsernameAuthenticationForm), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/", views.register, name="register"),
    path("profile/", views.profile, name="profile"),
    path("onboarding/", views.onboarding, name="onboarding"),
    path("onboarding/done/", views.onboarding_done, name="onboarding_done"),
    path("onboarding/<slug:step>/", views.onboarding_step, name="onboarding_step"),
    path("addresses/add/", views.add_address, name="add_address"),
    path("addresses/<int:address_id>/edit/", views.edit_address, name="edit_address"),
    path("addresses/<int:address_id>/delete/", views.delete_address, name="delete_address"),
]
