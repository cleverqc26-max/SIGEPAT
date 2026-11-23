from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, UserChangeForm

from .models import Usuario


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control", "autofocus": True}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}))


class UsuarioCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = (
            "username", "first_name", "last_name", "email",
            "dni", "telefono", "rol", "unidad_organica",
        )
        widgets = {
            "rol": forms.Select(attrs={"class": "form-select"}),
            "unidad_organica": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre, campo in self.fields.items():
            campo.widget.attrs.setdefault("class", "form-control")


class UsuarioChangeForm(UserChangeForm):
    password = None  # el cambio de contraseña se gestiona aparte

    class Meta:
        model = Usuario
        fields = (
            "username", "first_name", "last_name", "email",
            "dni", "telefono", "rol", "unidad_organica", "is_active",
        )
        widgets = {
            "rol": forms.Select(attrs={"class": "form-select"}),
            "unidad_organica": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre, campo in self.fields.items():
            if nombre != "is_active":
                campo.widget.attrs.setdefault("class", "form-control")
