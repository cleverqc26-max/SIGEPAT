from django.contrib import admin

from .models import RegistroConservacion


@admin.register(RegistroConservacion)
class RegistroConservacionAdmin(admin.ModelAdmin):
    list_display = ("bien", "estado", "fecha_registro", "registrado_por")
    list_filter = ("estado",)
    search_fields = ("bien__codigo_patrimonial",)
