from django.conf import settings
from django.db import models

from catalogos.models import CategoriaBien, UnidadOrganica


class Bien(models.Model):
    """
    RF06-RF10: registro y codificación de bienes muebles patrimoniales.
    """

    TIPO_ADQUISICION = [
        ("COMPRA", "Compra / adquisición"),
        ("DONACION", "Donación"),
        ("TRANSFERENCIA", "Transferencia"),
        ("SANEAMIENTO", "Saneamiento"),
    ]
    ESTADO_SITUACION = [
        ("ACTIVO", "Activo"),
        ("BAJA", "Dado de baja"),
    ]

    codigo_patrimonial = models.CharField(max_length=20, unique=True, editable=False)
    denominacion = models.CharField(max_length=150)
    marca = models.CharField(max_length=80, blank=True)
    modelo = models.CharField(max_length=80, blank=True)
    serie = models.CharField(max_length=80, blank=True)
    categoria = models.ForeignKey(CategoriaBien, on_delete=models.PROTECT, related_name="bienes")
    unidad_organica = models.ForeignKey(
        UnidadOrganica, on_delete=models.PROTECT, related_name="bienes",
        help_text="Unidad orgánica donde se ubica actualmente el bien.",
    )
    valor_adquisicion = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_alta = models.DateField()
    tipo_adquisicion = models.CharField(max_length=20, choices=TIPO_ADQUISICION, default="COMPRA")
    descripcion = models.TextField(blank=True)
    situacion = models.CharField(max_length=10, choices=ESTADO_SITUACION, default="ACTIVO")

    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="bienes_registrados"
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bien patrimonial"
        verbose_name_plural = "Bienes patrimoniales"
        ordering = ["-fecha_registro"]

    def __str__(self):
        return f"{self.codigo_patrimonial} - {self.denominacion}"

    def generar_codigo(self):
        """
        RF07: código patrimonial único, formato:
        UAA-<categoria_id 2 dígitos>-<correlativo 6 dígitos>-<año>
        """
        anio = self.fecha_alta.year if self.fecha_alta else 0
        correlativo = Bien.objects.filter(categoria=self.categoria).count() + 1
        return f"UAA-{self.categoria_id:02d}-{correlativo:06d}-{anio}"

    def save(self, *args, **kwargs):
        if not self.codigo_patrimonial:
            self.codigo_patrimonial = self.generar_codigo()
        super().save(*args, **kwargs)

    @property
    def responsable_actual(self):
        asignacion = self.asignaciones.filter(activa=True).order_by("-fecha_asignacion").first()
        return asignacion.responsable if asignacion else None

    @property
    def estado_conservacion_actual(self):
        registro = self.registros_conservacion.order_by("-fecha_registro").first()
        return registro.get_estado_display() if registro else "Sin registrar"


class DocumentoRespaldo(models.Model):
    """RF08: documentos y ficha técnica que sustentan el registro del bien."""

    TIPOS = [
        ("FICHA_TECNICA", "Ficha técnica"),
        ("COMPROBANTE", "Comprobante de adquisición"),
        ("ACTA", "Acta / resolución"),
        ("OTRO", "Otro documento"),
    ]

    bien = models.ForeignKey(Bien, on_delete=models.CASCADE, related_name="documentos")
    tipo_documento = models.CharField(max_length=20, choices=TIPOS, default="FICHA_TECNICA")
    archivo = models.FileField(upload_to="documentos_bienes/%Y/%m/")
    descripcion = models.CharField(max_length=200, blank=True)
    cargado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    fecha_carga = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Documento de respaldo"
        verbose_name_plural = "Documentos de respaldo"
        ordering = ["-fecha_carga"]

    def __str__(self):
        return f"{self.bien.codigo_patrimonial} - {self.get_tipo_documento_display()}"


class HistorialCambioBien(models.Model):
    """RF09: auditoría de modificaciones sobre la ficha de un bien."""

    bien = models.ForeignKey(Bien, on_delete=models.CASCADE, related_name="historial_cambios")
    campo_modificado = models.CharField(max_length=80)
    valor_anterior = models.CharField(max_length=255, blank=True)
    valor_nuevo = models.CharField(max_length=255, blank=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Historial de cambio"
        verbose_name_plural = "Historial de cambios"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.bien.codigo_patrimonial}: {self.campo_modificado}"
