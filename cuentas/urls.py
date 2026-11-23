from django.urls import path

from . import views

app_name = "cuentas"

urlpatterns = [
    path("login/", views.LoginUsuarioView.as_view(), name="login"),
    path("logout/", views.LogoutUsuarioView.as_view(), name="logout"),
    path("usuarios/", views.ListaUsuariosView.as_view(), name="lista_usuarios"),
    path("usuarios/nuevo/", views.CrearUsuarioView.as_view(), name="crear_usuario"),
    path("usuarios/<int:pk>/editar/", views.EditarUsuarioView.as_view(), name="editar_usuario"),
]
