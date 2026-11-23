from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from catalogos.models import Rol
from .forms import LoginForm, UsuarioChangeForm, UsuarioCreationForm
from .mixins import RolRequeridoMixin
from .models import Usuario


class LoginUsuarioView(LoginView):
    """RF01: inicio de sesión con usuario y contraseña."""

    template_name = "cuentas/login.html"
    redirect_authenticated_user = True
    authentication_form = LoginForm

    def form_invalid(self, form):
        messages.error(self.request, "Usuario o contraseña incorrectos.")
        return super().form_invalid(form)


class LogoutUsuarioView(LogoutView):
    next_page = reverse_lazy("cuentas:login")


class ListaUsuariosView(RolRequeridoMixin, ListView):
    """RF02: administración de cuentas de usuario (solo Administrador)."""

    model = Usuario
    template_name = "cuentas/lista_usuarios.html"
    context_object_name = "usuarios"
    paginate_by = 20
    roles_permitidos = (Rol.ADMINISTRADOR,)

    def get_queryset(self):
        qs = Usuario.objects.select_related("rol", "unidad_organica").order_by("username")
        busqueda = self.request.GET.get("q")
        if busqueda:
            qs = qs.filter(username__icontains=busqueda)
        return qs


class CrearUsuarioView(RolRequeridoMixin, CreateView):
    model = Usuario
    form_class = UsuarioCreationForm
    template_name = "cuentas/form_usuario.html"
    success_url = reverse_lazy("cuentas:lista_usuarios")
    roles_permitidos = (Rol.ADMINISTRADOR,)

    def form_valid(self, form):
        messages.success(self.request, "Usuario creado correctamente.")
        return super().form_valid(form)


class EditarUsuarioView(RolRequeridoMixin, UpdateView):
    """RF02: editar y activar/desactivar cuentas de usuario."""

    model = Usuario
    form_class = UsuarioChangeForm
    template_name = "cuentas/form_usuario.html"
    success_url = reverse_lazy("cuentas:lista_usuarios")
    roles_permitidos = (Rol.ADMINISTRADOR,)

    def form_valid(self, form):
        messages.success(self.request, "Usuario actualizado correctamente.")
        return super().form_valid(form)
