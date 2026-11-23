"""
Tablas de catálogo (dominio finito, definido por la normativa o la
estructura de la entidad). No se siembran con 100 registros porque su
cardinalidad real es pequeña: lo que exige la tesis es que las tablas
*principales* (bienes, asignaciones, desplazamientos, inventario, etc.)
tengan ese volumen de datos de prueba.
"""
from django.db import models


class Rol(models.Model):
    """RF03: perfiles de acceso del sistema."""

    ADMINISTRADOR = "ADMINISTRADOR"
    CONTROL_PATRIMONIAL = "CONTROL_PATRIMONIAL"
    ALMACEN = "ALMACEN"
    CONTABILIDAD = "CONTABILIDAD"
    RESPONSABLE = "RESPONSABLE"
    JEFATURA = "JEFATURA"

    codigo = models.CharField(max_length=30, unique=True)
    nombre = models.CharField(max_length=80)
    descripcion = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Rol"
        verbose_name_plural = "Roles"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class UnidadOrganica(models.Model):
    """Oficinas / áreas de la Municipalidad Distrital de Unión Asháninka."""

    nombre = models.CharField(max_length=120, unique=True)
    siglas = models.CharField(max_length=15, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Unidad orgánica"
        verbose_name_plural = "Unidades orgánicas"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class CategoriaBien(models.Model):
    """Clasificación de bienes muebles patrimoniales (catálogo institucional)."""

    nombre = models.CharField(max_length=120, unique=True)
    vida_util_anios = models.PositiveSmallIntegerField(
        default=5, help_text="Referencial, para el cálculo de depreciación."
    )

    class Meta:
        verbose_name = "Categoría de bien"
        verbose_name_plural = "Categorías de bienes"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class CausalBaja(models.Model):
    """RF25: causales de baja según la Directiva N.° 0006-2021-EF/54.01."""

    nombre = models.CharField(max_length=120, unique=True)
    descripcion = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Causal de baja"
        verbose_name_plural = "Causales de baja"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre
