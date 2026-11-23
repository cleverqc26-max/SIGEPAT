"""
RF05 / RNF12: registra en RegistroAcceso cada intento de inicio de sesión
(exitoso o fallido), conectándose a las señales de autenticación de Django.
Se implementa como "middleware" del proyecto porque conecta las señales al
arrancar la aplicación (patrón recomendado por Django); el registro en sí
ocurre vía señales, no en el ciclo request/response.
"""
from django.contrib.auth.signals import user_logged_in, user_login_failed


def _get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _on_login(sender, request, user, **kwargs):
    from cuentas.models import RegistroAcceso

    RegistroAcceso.objects.create(
        usuario=user,
        username_ingresado=user.get_username(),
        exitoso=True,
        direccion_ip=_get_client_ip(request) if request else None,
    )


def _on_login_failed(sender, credentials, request=None, **kwargs):
    from cuentas.models import RegistroAcceso

    RegistroAcceso.objects.create(
        usuario=None,
        username_ingresado=credentials.get("username", ""),
        exitoso=False,
        direccion_ip=_get_client_ip(request) if request else None,
    )


user_logged_in.connect(_on_login, dispatch_uid="auditoria_on_login")
user_login_failed.connect(_on_login_failed, dispatch_uid="auditoria_on_login_failed")


class RegistroAccesoMiddleware:
    """Middleware "no-op": su única función es asegurar, al cargarse el
    proyecto, que este módulo se importe y las señales queden conectadas."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)
