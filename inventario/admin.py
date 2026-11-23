from django.contrib import admin

from .models import Inventario, VerificacionInventario


class VerificacionInline(admin.TabularInline):
    model = VerificacionInventario
    extra = 0


@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = ("anio", "unidad_organica", "estado", "fecha_inicio", "fecha_cierre", "responsable")
    list_filter = ("estado", "anio", "unidad_organica")


@admin.register(VerificacionInventario)
class VerificacionInventarioAdmin(admin.ModelAdmin):
    list_display = ("inventario", "bien", "resultado", "fecha_verificacion", "verificado_por")
    list_filter = ("resultado",)
