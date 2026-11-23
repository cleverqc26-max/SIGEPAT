from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(pattern_name="dashboard:panel", permanent=False)),
    path("cuentas/", include("cuentas.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("bienes/", include("bienes.urls")),
    path("asignaciones/", include("asignaciones.urls")),
    path("desplazamientos/", include("desplazamientos.urls")),
    path("conservacion/", include("conservacion.urls")),
    path("inventario/", include("inventario.urls")),
    path("bajas/", include("bajas.urls")),
    path("reportes/", include("reportes.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
