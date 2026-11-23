from django.contrib import admin

from .models import Desplazamiento


@admin.register(Desplazamiento)
class DesplazamientoAdmin(admin.ModelAdmin):
    list_display = ("bien", "tipo", "estado", "solicitante", "fecha_solicitud")
    list_filter = ("tipo", "estado")
    search_fields = ("bien__codigo_patrimonial",)
