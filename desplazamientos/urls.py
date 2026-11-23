from django.urls import path

from . import views

app_name = "desplazamientos"

urlpatterns = [
    path("", views.ListaDesplazamientosView.as_view(), name="lista"),
    path("excel/", views.ExportarDesplazamientosExcelView.as_view(), name="exportar_excel"),
    path("bien/<int:bien_pk>/nuevo/", views.CrearDesplazamientoView.as_view(), name="crear"),
    path("<int:pk>/resolver/", views.ResolverDesplazamientoView.as_view(), name="resolver"),
]
