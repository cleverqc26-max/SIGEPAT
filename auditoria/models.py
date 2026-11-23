from django.conf import settings
from django.db import models


class LogAuditoria(models.Model):
    """RNF12: log de auditoría de operaciones críticas del sistema."""

    ACCIONES = [
        ("ALTA_BIEN", "Alta de bien"),
        ("EDICION_BIEN", "Edición de bien"),
        ("BAJA_BIEN", "Baja de bien"),
        ("ASIGNACION", "Asignación de bien"),
        ("REASIGNACION", "Reasignación de bien"),
        ("DESPLAZAMIENTO_SOLICITADO", "Desplazamiento solicitado"),
        ("DESPLAZAMIENTO_APROBADO", "Desplazamiento aprobado"),
        ("DESPLAZAMIENTO_RECHAZADO", "Desplazamiento rechazado"),
        ("INVENTARIO_ABIERTO", "Apertura de inventario"),
        ("INVENTARIO_CERRADO", "Cierre de inventario"),
        ("SANEAMIENTO", "Actualización de saneamiento"),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="acciones_auditadas"
    )
    accion = models.CharField(max_length=40, choices=ACCIONES)
    modelo_afectado = models.CharField(max_length=60)
    objeto_id = models.CharField(max_length=30, blank=True)
    detalle = models.CharField(max_length=255, blank=True)
    fecha_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Registro de auditoría"
        verbose_name_plural = "Registros de auditoría"
        ordering = ["-fecha_hora"]

    def __str__(self):
        return f"{self.fecha_hora:%Y-%m-%d %H:%M} - {self.get_accion_display()} - {self.modelo_afectado}#{self.objeto_id}"


def registrar_auditoria(usuario, accion, modelo_afectado, objeto_id="", detalle=""):
    """Helper usado desde las vistas para dejar trazabilidad de operaciones críticas."""
    return LogAuditoria.objects.create(
        usuario=usuario if getattr(usuario, "is_authenticated", False) else None,
        accion=accion,
        modelo_afectado=modelo_afectado,
        objeto_id=str(objeto_id),
        detalle=detalle,
    )
