from django.urls import path

from . import views

app_name = "asignaciones"

urlpatterns = [
    path("", views.ListaAsignacionesView.as_view(), name="lista"),
    path("bien/<int:bien_pk>/nueva/", views.CrearAsignacionView.as_view(), name="crear"),
]
