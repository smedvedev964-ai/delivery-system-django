from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AddressStepForm, NameStepForm, PhoneStepForm, ProfileForm, RegistrationForm
from .models import Address


def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:profile")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Аккаунт создан. Давайте быстро настроим профиль.")
        return redirect("accounts:onboarding")
    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Контактные данные сохранены.")
        return redirect("accounts:profile")
    return render(request, "accounts/profile.html", {
        "form": form,
        "has_name": bool(request.user.first_name),
        "has_phone": bool(request.user.phone),
    })


ONBOARDING_STEPS = ("name", "phone")


@login_required
def onboarding(request):
    if not request.user.first_name:
        return redirect("accounts:onboarding_step", step="name")
    if not request.user.phone:
        return redirect("accounts:onboarding_step", step="phone")
    return redirect("accounts:onboarding_done")


@login_required
def onboarding_step(request, step):
    if step not in ONBOARDING_STEPS:
        return redirect("accounts:onboarding")
    form_classes = {"name": NameStepForm, "phone": PhoneStepForm}
    form = form_classes[step](request.POST or None, instance=request.user)

    if request.method == "POST":
        if "skip" in request.POST:
            messages.info(request, "Этот шаг можно заполнить позже в профиле.")
            return _next_onboarding_step(step)
        if form.is_valid():
            form.save()
            messages.success(request, "Сохранено.")
            return _next_onboarding_step(step)

    titles = {
        "name": "Как вас зовут?",
        "phone": "Номер телефона",
    }
    return render(request, "accounts/onboarding_step.html", {
        "form": form,
        "step": step,
        "step_number": ONBOARDING_STEPS.index(step) + 1,
        "step_count": len(ONBOARDING_STEPS),
        "title": titles[step],
    })


def _next_onboarding_step(step):
    next_index = ONBOARDING_STEPS.index(step) + 1
    if next_index < len(ONBOARDING_STEPS):
        return redirect("accounts:onboarding_step", step=ONBOARDING_STEPS[next_index])
    return redirect("accounts:onboarding_done")


@login_required
def onboarding_done(request):
    return render(request, "accounts/onboarding_done.html")


@login_required
def add_address(request):
    address = Address.objects.filter(user=request.user).first()
    form = AddressStepForm(request.POST or None, instance=address)
    if request.method == "POST" and form.is_valid():
        saved_address = form.save(commit=False)
        saved_address.user = request.user
        saved_address.is_default = True
        saved_address.save()
        messages.success(request, "Адрес доставки сохранён.")
        return redirect("home")
    return render(request, "accounts/address_form.html", {"form": form, "address": address})


@login_required
def edit_address(request, address_id):
    address = get_object_or_404(Address, pk=address_id, user=request.user)
    form = AddressStepForm(request.POST or None, instance=address)
    if request.method == "POST" and form.is_valid():
        saved_address = form.save(commit=False)
        saved_address.is_default = True
        saved_address.save()
        messages.success(request, "Адрес доставки обновлён.")
        return redirect("home")
    return render(request, "accounts/address_form.html", {"form": form, "address": address})


@login_required
def delete_address(request, address_id):
    if request.method == "POST":
        address = get_object_or_404(Address, pk=address_id, user=request.user)
        address.delete()
        messages.success(request, "Адрес удалён.")
    return redirect("accounts:profile")
