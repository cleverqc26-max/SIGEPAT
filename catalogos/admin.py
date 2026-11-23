from django.contrib import admin

from .models import CategoriaBien, CausalBaja, Rol, UnidadOrganica


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre")
    search_fields = ("codigo", "nombre")


@admin.register(UnidadOrganica)
class UnidadOrganicaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "siglas", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre", "siglas")


@admin.register(CategoriaBien)
class CategoriaBienAdmin(admin.ModelAdmin):
    list_display = ("nombre", "vida_util_anios")
    search_fields = ("nombre",)


@admin.register(CausalBaja)
class CausalBajaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "descripcion")
    search_fields = ("nombre",)
