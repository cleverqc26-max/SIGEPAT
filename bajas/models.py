from django.conf import settings
from django.db import models

from bienes.models import Bien
from catalogos.models import CausalBaja
from inventario.models import VerificacionInventario


class Baja(models.Model):
    """RF25-RF26: baja y disposición final de un bien."""

    bien = models.OneToOneField(Bien, on_delete=models.CASCADE, related_name="baja")
    causal = models.ForeignKey(CausalBaja, on_delete=models.PROTECT, related_name="bajas")
    fecha_baja = models.DateField()
    disposicion_final = models.CharField(
        max_length=30,
        choices=[
            ("REMATE", "Remate"),
            ("DONACION", "Donación"),
            ("DESTRUCCION", "Destrucción"),
            ("TRANSFERENCIA", "Transferencia"),
            ("PENDIENTE", "Pendiente de definir"),
        ],
        default="PENDIENTE",
    )
    documentacion_sustento = models.FileField(upload_to="bajas/%Y/%m/", null=True, blank=True)
    observaciones = models.CharField(max_length=255, blank=True)
    registrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Baja de bien"
        verbose_name_plural = "Bajas de bienes"
        ordering = ["-fecha_baja"]

    def __str__(self):
        return f"Baja {self.bien.codigo_patrimonial} - {self.causal}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.bien.situacion != "BAJA":
            self.bien.situacion = "BAJA"
            self.bien.save(update_fields=["situacion"])


class Saneamiento(models.Model):
    """RF27: saneamiento administrativo de bienes sobrantes y faltantes."""

    TIPO = [("SOBRANTE", "Sobrante"), ("FALTANTE", "Faltante")]
    ESTADO_TRAMITE = [
        ("PENDIENTE", "Pendiente"),
        ("EN_PROCESO", "En proceso"),
        ("CONCLUIDO", "Concluido"),
    ]

    verificacion = models.OneToOneField(
        VerificacionInventario, on_delete=models.CASCADE, related_name="saneamiento"
    )
    tipo = models.CharField(max_length=10, choices=TIPO)
    estado_tramite = models.CharField(max_length=12, choices=ESTADO_TRAMITE, default="PENDIENTE")
    plazo_normativo_dias = models.PositiveSmallIntegerField(default=30)
    fecha_inicio_tramite = models.DateField()
    fecha_resolucion = models.DateField(null=True, blank=True)
    observaciones = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Saneamiento administrativo"
        verbose_name_plural = "Saneamientos administrativos"
        ordering = ["-fecha_inicio_tramite"]

    def __str__(self):
        return f"Saneamiento {self.get_tipo_display()} - {self.verificacion}"
