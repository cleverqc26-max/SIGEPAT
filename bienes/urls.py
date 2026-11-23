from django.urls import path

from . import views

app_name = "bienes"

urlpatterns = [
    path("", views.ListaBienesView.as_view(), name="lista"),
    path("nuevo/", views.CrearBienView.as_view(), name="crear"),
    path("<int:pk>/", views.DetalleBienView.as_view(), name="detalle"),
    path("<int:pk>/editar/", views.EditarBienView.as_view(), name="editar"),
    path("<int:pk>/documentos/nuevo/", views.SubirDocumentoView.as_view(), name="subir_documento"),
]
