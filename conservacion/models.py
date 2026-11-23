from django.conf import settings
from django.db import models

from bienes.models import Bien


class RegistroConservacion(models.Model):
    """RF18-RF19: estado de conservación de un bien, con evidencia fotográfica."""

    ESTADOS = [
        ("NUEVO", "Nuevo"),
        ("BUENO", "Bueno"),
        ("REGULAR", "Regular"),
        ("MALO", "Malo"),
        ("CHATARRA", "Chatarra"),
    ]

    bien = models.ForeignKey(Bien, on_delete=models.CASCADE, related_name="registros_conservacion")
    estado = models.CharField(max_length=10, choices=ESTADOS)
    observaciones = models.CharField(max_length=255, blank=True)
    evidencia_foto = models.ImageField(upload_to="conservacion/%Y/%m/", null=True, blank=True)
    registrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Registro de conservación"
        verbose_name_plural = "Registros de conservación"
        ordering = ["-fecha_registro"]

    def __str__(self):
        return f"{self.bien.codigo_patrimonial}: {self.get_estado_display()}"
