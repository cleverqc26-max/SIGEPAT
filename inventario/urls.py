from django.urls import path

from . import views

app_name = "inventario"

urlpatterns = [
    path("", views.ListaInventariosView.as_view(), name="lista"),
    path("nuevo/", views.CrearInventarioView.as_view(), name="crear"),
    path("<int:pk>/", views.DetalleInventarioView.as_view(), name="detalle"),
    path("<int:pk>/verificar/", views.RegistrarVerificacionView.as_view(), name="verificar"),
    path("<int:pk>/cerrar/", views.CerrarInventarioView.as_view(), name="cerrar"),
    path("<int:pk>/conciliar/", views.ConciliarInventarioView.as_view(), name="conciliar"),
]
