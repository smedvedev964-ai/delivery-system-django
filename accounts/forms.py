import uuid
import re

from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Address

User = get_user_model()


class RegistrationForm(forms.Form):
    email = forms.EmailField(label="Электронная почта")
    password1 = forms.CharField(label="Пароль", widget=forms.PasswordInput, strip=False)
    password2 = forms.CharField(label="Повторите пароль", widget=forms.PasswordInput, strip=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Аккаунт с такой почтой уже зарегистрирован.")
        return email

    def clean(self):
        cleaned = super().clean()
        password1, password2 = cleaned.get("password1"), cleaned.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Пароли не совпадают.")
        if password1:
            try:
                validate_password(password1)
            except ValidationError as exc:
                self.add_error("password1", exc)
        return cleaned

    def save(self):
        email = self.cleaned_data["email"]
        # Username remains an internal Django identifier; customers sign in with email.
        username = f"client_{uuid.uuid4().hex}"
        return User.objects.create_user(
            username=username,
            email=email,
            password=self.cleaned_data["password1"],
            role=User.Role.CLIENT,
        )


class EmailOrUsernameAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Электронная почта или логин",
        widget=forms.TextInput(attrs={"autofocus": True}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

    def clean(self):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")
        if username and password:
            try:
                user = User.objects.get(email__iexact=username.strip())
                username = user.get_username()
            except User.DoesNotExist:
                pass
            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            self.confirm_login_allowed(self.user_cache)
        return self.cleaned_data


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "phone")
        labels = {
            "first_name": "Имя",
            "last_name": "Фамилия",
            "email": "Электронная почта",
            "phone": "Телефон",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Эта почта уже используется другим аккаунтом.")
        return email

    def clean_phone(self):
        return _clean_phone(self.cleaned_data["phone"])


class NameStepForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name")
        labels = {"first_name": "Имя", "last_name": "Фамилия"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})


class PhoneStepForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("phone",)
        labels = {"phone": "Номер телефона"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["phone"].required = True
        self.fields["phone"].widget.attrs.update({"class": "form-control", "placeholder": "+7 900 000-00-00", "autocomplete": "tel"})

    def clean_phone(self):
        return _clean_phone(self.cleaned_data["phone"])


def _clean_phone(phone):
    phone = phone.strip()
    digits = re.sub(r"\D", "", phone)
    if phone and (not re.fullmatch(r"\+?[0-9\s()\-]+", phone) or len(digits) < 10):
        raise ValidationError("Введите телефон минимум из 10 цифр.")
    return phone


class AddressStepForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ("city", "street", "house", "apartment", "comment")
        labels = {
            "city": "Город",
            "street": "Улица",
            "house": "Дом",
            "apartment": "Квартира",
            "comment": "Как вас найти",
        }
        widgets = {"comment": forms.TextInput(attrs={"placeholder": "Подъезд, этаж, код домофона"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
