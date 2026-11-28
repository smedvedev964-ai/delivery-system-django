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
    addresses = Address.objects.filter(user=request.user)
    return render(request, "accounts/profile.html", {
        "form": form,
        "addresses": addresses,
        "has_name": bool(request.user.first_name),
        "has_phone": bool(request.user.phone),
        "has_address": addresses.exists(),
    })


ONBOARDING_STEPS = ("name", "phone", "address")


@login_required
def onboarding(request):
    if not request.user.first_name:
        return redirect("accounts:onboarding_step", step="name")
    if not request.user.phone:
        return redirect("accounts:onboarding_step", step="phone")
    if not Address.objects.filter(user=request.user).exists():
        return redirect("accounts:onboarding_step", step="address")
    return redirect("accounts:onboarding_done")


@login_required
def onboarding_step(request, step):
    if step not in ONBOARDING_STEPS:
        return redirect("accounts:onboarding")
    form_classes = {"name": NameStepForm, "phone": PhoneStepForm}
    if step in form_classes:
        form = form_classes[step](request.POST or None, instance=request.user)
    else:
        form = AddressStepForm(request.POST or None)

    if request.method == "POST":
        if "skip" in request.POST:
            messages.info(request, "Этот шаг можно заполнить позже в профиле.")
            return _next_onboarding_step(step)
        if form.is_valid():
            if step == "address":
                address = form.save(commit=False)
                address.user = request.user
                address.is_default = not Address.objects.filter(user=request.user).exists()
                address.save()
            else:
                form.save()
            messages.success(request, "Сохранено.")
            return _next_onboarding_step(step)

    titles = {
        "name": ("Как к вам обращаться?", "Имя поможет нам подписывать ваши заказы."),
        "phone": ("Как с вами связаться?", "Телефон пригодится курьеру, если нужно уточнить доставку."),
        "address": ("Куда доставлять?", "Адрес сохранится в профиле. Его можно будет изменить перед заказом."),
    }
    return render(request, "accounts/onboarding_step.html", {
        "form": form,
        "step": step,
        "step_number": ONBOARDING_STEPS.index(step) + 1,
        "step_count": len(ONBOARDING_STEPS),
        "title": titles[step][0],
        "description": titles[step][1],
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
    form = AddressStepForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        address = form.save(commit=False)
        address.user = request.user
        address.is_default = not Address.objects.filter(user=request.user).exists()
        address.save()
        messages.success(request, "Адрес добавлен в профиль.")
        return redirect("accounts:profile")
    return render(request, "accounts/address_form.html", {"form": form})


@login_required
def edit_address(request, address_id):
    address = get_object_or_404(Address, pk=address_id, user=request.user)
    form = AddressStepForm(request.POST or None, instance=address)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Адрес обновлён.")
        return redirect("accounts:profile")
    return render(request, "accounts/address_form.html", {"form": form, "address": address})


@login_required
def delete_address(request, address_id):
    if request.method == "POST":
        address = get_object_or_404(Address, pk=address_id, user=request.user)
        address.delete()
        messages.success(request, "Адрес удалён.")
    return redirect("accounts:profile")
