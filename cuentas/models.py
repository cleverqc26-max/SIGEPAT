from django.contrib.auth.models import AbstractUser
from django.db import models

from catalogos.models import Rol, UnidadOrganica


class Usuario(AbstractUser):
    """
    RF01-RF04: usuario del sistema con perfil (rol) y unidad orgánica.
    Django ya cifra la contraseña (RNF11) y controla la sesión.
    """

    rol = models.ForeignKey(
        Rol, on_delete=models.PROTECT, related_name="usuarios",
        null=True, blank=True,
    )
    unidad_organica = models.ForeignKey(
        UnidadOrganica, on_delete=models.SET_NULL, related_name="usuarios",
        null=True, blank=True,
    )
    dni = models.CharField(max_length=8, blank=True)
    telefono = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        nombre = self.get_full_name() or self.username
        return f"{nombre} ({self.rol.nombre if self.rol_id else 'sin rol'})"

    # --- helpers de autorización usados por las vistas (RF04) ---
    def tiene_rol(self, *codigos):
        return bool(self.rol_id) and self.rol.codigo in codigos

    @property
    def es_administrador(self):
        return self.tiene_rol(Rol.ADMINISTRADOR) or self.is_superuser

    @property
    def es_control_patrimonial(self):
        return self.tiene_rol(Rol.CONTROL_PATRIMONIAL)

    @property
    def es_jefatura(self):
        return self.tiene_rol(Rol.JEFATURA)

    @property
    def es_contabilidad(self):
        return self.tiene_rol(Rol.CONTABILIDAD)

    @property
    def es_almacen(self):
        return self.tiene_rol(Rol.ALMACEN)

    @property
    def es_responsable(self):
        return self.tiene_rol(Rol.RESPONSABLE)

    # --- RF04: restringir el acceso a los MÓDULOS (no solo a las acciones de
    # creación/edición, que ya filtraba RolRequeridoMixin) según el perfil del
    # usuario autenticado. El mapeo se basa en el "Usuario" declarado para
    # cada Historia de Usuario en Requisitos_RF_RNF_HU_SistemaBienesPatrimoniales
    # (versión "V OK"): HU-06 habilita a Almacén/Contabilidad a buscar bienes;
    # HU-09 habilita al servidor responsable a solicitar desplazamientos;
    # HU-16 habilita a Jefatura a ver reportes y el dashboard general.
    MODULOS_POR_ROL = {
        Rol.CONTROL_PATRIMONIAL: {"bienes", "asignaciones", "desplazamientos", "inventario", "bajas", "reportes"},
        Rol.ALMACEN: {"bienes", "reportes"},
        Rol.CONTABILIDAD: {"bienes", "inventario", "reportes"},
        Rol.RESPONSABLE: {"asignaciones", "desplazamientos"},
        Rol.JEFATURA: {"reportes"},
    }
    TODOS_LOS_MODULOS = {"bienes", "asignaciones", "desplazamientos", "inventario", "bajas", "reportes"}

    @property
    def modulos_visibles(self):
        """RF04/HU-02: módulos del menú de navegación habilitados para el perfil.
        El administrador ve todos; el resto solo los módulos donde su rol
        tiene una función de negocio real (ver MODULOS_POR_ROL)."""
        if self.es_administrador:
            return self.TODOS_LOS_MODULOS
        if self.rol_id and self.rol.codigo in self.MODULOS_POR_ROL:
            return self.MODULOS_POR_ROL[self.rol.codigo]
        return set()


class RegistroAcceso(models.Model):
    """RF05: historial de accesos (usuario, fecha, hora, acción)."""

    usuario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name="accesos", null=True, blank=True
    )
    username_ingresado = models.CharField(max_length=150, blank=True)
    exitoso = models.BooleanField(default=True)
    direccion_ip = models.GenericIPAddressField(null=True, blank=True)
    fecha_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Registro de acceso"
        verbose_name_plural = "Registros de acceso"
        ordering = ["-fecha_hora"]

    def __str__(self):
        estado = "OK" if self.exitoso else "FALLIDO"
        return f"{self.username_ingresado} - {estado} - {self.fecha_hora:%Y-%m-%d %H:%M}"
