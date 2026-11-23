from django.contrib import admin

from .models import LogAuditoria


@admin.register(LogAuditoria)
class LogAuditoriaAdmin(admin.ModelAdmin):
    list_display = ("fecha_hora", "usuario", "accion", "modelo_afectado", "objeto_id")
    list_filter = ("accion",)
    search_fields = ("modelo_afectado", "objeto_id", "detalle")
    date_hierarchy = "fecha_hora"
