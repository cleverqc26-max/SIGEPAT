from django.conf import settings
from django.db import models

from bienes.models import Bien


class Desplazamiento(models.Model):
    """RF14-RF17: control de desplazamientos internos y externos de un bien."""

    TIPO = [("INTERNO", "Interno (entre oficinas)"), ("EXTERNO", "Externo (fuera de la sede)")]
    ESTADO = [
        ("PENDIENTE", "Pendiente de autorización"),
        ("APROBADO", "Aprobado"),
        ("RECHAZADO", "Rechazado"),
    ]

    bien = models.ForeignKey(Bien, on_delete=models.CASCADE, related_name="desplazamientos")
    solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="desplazamientos_solicitados"
    )
    tipo = models.CharField(max_length=10, choices=TIPO, default="INTERNO")
    origen = models.CharField(max_length=150)
    destino = models.CharField(max_length=150)
    motivo = models.CharField(max_length=255, blank=True)
    estado = models.CharField(max_length=10, choices=ESTADO, default="PENDIENTE")
    autorizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="desplazamientos_autorizados",
    )
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_resolucion = models.DateTimeField(null=True, blank=True)
    observaciones_resolucion = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Desplazamiento"
        verbose_name_plural = "Desplazamientos"
        ordering = ["-fecha_solicitud"]

    def __str__(self):
        return f"{self.bien.codigo_patrimonial}: {self.origen} -> {self.destino} ({self.get_estado_display()})"

    def aprobar(self, usuario, fecha_resolucion):
        """RF15-RF16: al aprobar, se actualiza la ubicación (unidad orgánica) del bien."""
        self.estado = "APROBADO"
        self.autorizado_por = usuario
        self.fecha_resolucion = fecha_resolucion
        self.save(update_fields=["estado", "autorizado_por", "fecha_resolucion"])

    def rechazar(self, usuario, fecha_resolucion, motivo=""):
        self.estado = "RECHAZADO"
        self.autorizado_por = usuario
        self.fecha_resolucion = fecha_resolucion
        self.observaciones_resolucion = motivo
        self.save(update_fields=["estado", "autorizado_por", "fecha_resolucion", "observaciones_resolucion"])
