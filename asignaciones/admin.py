from django.contrib import admin

from .models import Asignacion


@admin.register(Asignacion)
class AsignacionAdmin(admin.ModelAdmin):
    list_display = ("numero_acta", "bien", "responsable", "fecha_asignacion", "activa")
    list_filter = ("activa",)
    search_fields = ("numero_acta", "bien__codigo_patrimonial")
