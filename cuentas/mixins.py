"""RF04: restringir el acceso a los módulos y acciones según el perfil del usuario."""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class RolRequeridoMixin(LoginRequiredMixin, UserPassesTestMixin):
    roles_permitidos = ()  # códigos de Rol permitidos; vacío = cualquier usuario autenticado
    raise_exception = False

    def test_func(self):
        usuario = self.request.user
        if usuario.is_superuser:
            return True
        if not self.roles_permitidos:
            return True
        return usuario.tiene_rol(*self.roles_permitidos)

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        from django.contrib import messages
        from django.shortcuts import redirect

        messages.error(self.request, "No tienes permiso para acceder a ese módulo con tu perfil actual.")
        return redirect("dashboard:panel")
