from django.urls import path

from . import views

app_name = "bajas"

urlpatterns = [
    path("", views.PanelBajasSaneamientoView.as_view(), name="lista"),
    path("bien/<int:bien_pk>/nueva/", views.CrearBajaView.as_view(), name="crear"),
    path("<int:pk>/actualizar-disposicion/", views.ActualizarDisposicionBajaView.as_view(), name="actualizar_disposicion"),
    path("saneamiento/<int:verificacion_pk>/iniciar/", views.IniciarSaneamientoView.as_view(), name="iniciar_saneamiento"),
    path("saneamiento/<int:pk>/actualizar/", views.ActualizarSaneamientoView.as_view(), name="actualizar_saneamiento"),
]
