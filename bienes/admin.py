from django.contrib import admin

from .models import Bien, DocumentoRespaldo, HistorialCambioBien


class DocumentoRespaldoInline(admin.TabularInline):
    model = DocumentoRespaldo
    extra = 0


@admin.register(Bien)
class BienAdmin(admin.ModelAdmin):
    list_display = ("codigo_patrimonial", "denominacion", "categoria", "unidad_organica", "situacion", "fecha_alta")
    list_filter = ("situacion", "categoria", "unidad_organica")
    search_fields = ("codigo_patrimonial", "denominacion", "serie")
    inlines = [DocumentoRespaldoInline]


@admin.register(HistorialCambioBien)
class HistorialCambioBienAdmin(admin.ModelAdmin):
    list_display = ("bien", "campo_modificado", "usuario", "fecha")
    search_fields = ("bien__codigo_patrimonial",)
