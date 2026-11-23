from django.conf import settings
from django.db import models

from bienes.models import Bien


class Asignacion(models.Model):
    """RF11-RF13: asignación en uso de un bien a un servidor responsable."""

    bien = models.ForeignKey(Bien, on_delete=models.CASCADE, related_name="asignaciones")
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="bienes_asignados"
    )
    numero_acta = models.CharField(max_length=30, unique=True, editable=False)
    fecha_asignacion = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    activa = models.BooleanField(default=True)
    observaciones = models.CharField(max_length=255, blank=True)
    asignado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="asignaciones_realizadas"
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Asignación"
        verbose_name_plural = "Asignaciones"
        ordering = ["-fecha_asignacion"]

    def __str__(self):
        return f"Acta {self.numero_acta} - {self.bien.codigo_patrimonial}"

    def save(self, *args, **kwargs):
        if not self.numero_acta:
            correlativo = Asignacion.objects.count() + 1
            self.numero_acta = f"ASIG-{correlativo:06d}"
        super().save(*args, **kwargs)

    def cerrar(self, fecha_fin):
        """RF12: cierra la asignación vigente al reasignar el bien."""
        self.activa = False
        self.fecha_fin = fecha_fin
        self.save(update_fields=["activa", "fecha_fin"])
