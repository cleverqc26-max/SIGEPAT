from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import RegistroAcceso, Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ("username", "first_name", "last_name", "rol", "unidad_organica", "is_active")
    list_filter = ("rol", "unidad_organica", "is_active")
    fieldsets = UserAdmin.fieldsets + (
        ("Datos institucionales", {"fields": ("rol", "unidad_organica", "dni", "telefono")}),
    )


@admin.register(RegistroAcceso)
class RegistroAccesoAdmin(admin.ModelAdmin):
    list_display = ("username_ingresado", "usuario", "exitoso", "direccion_ip", "fecha_hora")
    list_filter = ("exitoso",)
    search_fields = ("username_ingresado",)
    date_hierarchy = "fecha_hora"
