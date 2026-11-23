from django.conf import settings
from django.db import models
from django.utils import timezone

from bienes.models import Bien
from catalogos.models import UnidadOrganica


class Inventario(models.Model):
    """RF20, RF23-RF24: proceso de inventario físico por periodo."""

    ESTADO = [("EN_PROCESO", "En proceso"), ("CERRADO", "Cerrado")]

    anio = models.PositiveIntegerField()
    unidad_organica = models.ForeignKey(UnidadOrganica, on_delete=models.PROTECT, related_name="inventarios")
    fecha_inicio = models.DateField()
    fecha_cierre = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=12, choices=ESTADO, default="EN_PROCESO")
    responsable = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="inventarios_a_cargo")
    conciliado_contabilidad = models.BooleanField(default=False, help_text="RF24: conciliación con contabilidad.")
    conciliado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="inventarios_conciliados",
        help_text="RF24: usuario (normalmente del rol Contabilidad) que registró la conciliación.",
    )
    fecha_conciliacion = models.DateTimeField(null=True, blank=True)
    observaciones_conciliacion = models.TextField(blank=True)
    observaciones_cierre = models.TextField(blank=True)

    class Meta:
        verbose_name = "Inventario físico"
        verbose_name_plural = "Inventarios físicos"
        ordering = ["-anio", "-fecha_inicio"]
        unique_together = ("anio", "unidad_organica")

    def __str__(self):
        return f"Inventario {self.anio} - {self.unidad_organica}"

    def cerrar(self, fecha_cierre, observaciones=""):
        """RF23: cierre formal del inventario."""
        self.estado = "CERRADO"
        self.fecha_cierre = fecha_cierre
        self.observaciones_cierre = observaciones
        self.save(update_fields=["estado", "fecha_cierre", "observaciones_cierre"])

    def conciliar(self, usuario, observaciones=""):
        """RF24: registra la conciliación entre el resultado del inventario
        físico ya cerrado y los registros de contabilidad. Flujo de negocio
        dedicado (antes solo era editable desde /admin/ de Django)."""
        self.conciliado_contabilidad = True
        self.conciliado_por = usuario
        self.fecha_conciliacion = timezone.now()
        self.observaciones_conciliacion = observaciones
        self.save(update_fields=[
            "conciliado_contabilidad", "conciliado_por", "fecha_conciliacion", "observaciones_conciliacion",
        ])

    @property
    def bienes_esperados(self):
        return Bien.objects.filter(unidad_organica=self.unidad_organica, situacion="ACTIVO")

    @property
    def total_esperado(self):
        return self.bienes_esperados.count()

    @property
    def total_verificado(self):
        return self.verificaciones.filter(resultado="ENCONTRADO").count()

    @property
    def total_sobrantes(self):
        return self.verificaciones.filter(resultado="SOBRANTE").count()

    @property
    def total_faltantes(self):
        return self.verificaciones.filter(resultado="FALTANTE").count()


class VerificacionInventario(models.Model):
    """RF21-RF22: verificación física de cada bien durante el inventario."""

    RESULTADOS = [
        ("ENCONTRADO", "Encontrado y conforme"),
        ("SOBRANTE", "Sobrante (hallado, no registrado)"),
        ("FALTANTE", "Faltante (registrado, no hallado)"),
    ]

    inventario = models.ForeignKey(Inventario, on_delete=models.CASCADE, related_name="verificaciones")
    bien = models.ForeignKey(
        Bien, on_delete=models.CASCADE, related_name="verificaciones_inventario", null=True, blank=True,
        help_text="Vacío cuando el resultado es SOBRANTE (bien no registrado previamente).",
    )
    descripcion_hallazgo = models.CharField(
        max_length=255, blank=True, help_text="Usado cuando el bien hallado no está registrado (sobrante)."
    )
    resultado = models.CharField(max_length=12, choices=RESULTADOS, default="ENCONTRADO")
    ubicacion_encontrada = models.CharField(max_length=150, blank=True)
    estado_conservacion_encontrado = models.CharField(max_length=10, blank=True)
    responsable_encontrado = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="verificaciones_como_responsable",
    )
    verificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="verificaciones_realizadas"
    )
    fecha_verificacion = models.DateTimeField(auto_now_add=True)
    origen_dispositivo = models.CharField(
        max_length=10, default="WEB", help_text="WEB o MOVIL, referencial para RF21/RNF07."
    )

    class Meta:
        verbose_name = "Verificación de inventario"
        verbose_name_plural = "Verificaciones de inventario"
        ordering = ["-fecha_verificacion"]

    def __str__(self):
        referencia = self.bien.codigo_patrimonial if self.bien_id else self.descripcion_hallazgo
        return f"{self.inventario}: {referencia} - {self.get_resultado_display()}"
