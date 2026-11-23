from django.contrib import admin

from .models import Baja, Saneamiento


@admin.register(Baja)
class BajaAdmin(admin.ModelAdmin):
    list_display = ("bien", "causal", "fecha_baja", "disposicion_final")
    list_filter = ("causal", "disposicion_final")


@admin.register(Saneamiento)
class SaneamientoAdmin(admin.ModelAdmin):
    list_display = ("verificacion", "tipo", "estado_tramite", "fecha_inicio_tramite")
    list_filter = ("tipo", "estado_tramite")
