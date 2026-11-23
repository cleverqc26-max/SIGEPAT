from django.urls import path

from . import views

app_name = "conservacion"

urlpatterns = [
    path("bien/<int:bien_pk>/nuevo/", views.CrearRegistroConservacionView.as_view(), name="crear"),
]
