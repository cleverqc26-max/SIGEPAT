"""
Configuración del proyecto SIGEPAT
(Sistema de Gestión y Control de Bienes Patrimoniales)

Municipalidad Distrital de Unión Asháninka, 2026
Arquitectura: Django (patrón MVT / MVC) + MySQL
"""
import os
from pathlib import Path

import pymysql

pymysql.install_as_MySQLdb()  # permite usar el driver puro-Python pymysql como si fuera mysqlclient

BASE_DIR = Path(__file__).resolve().parent.parent

# --------------------------------------------------------------------------
# Variables de entorno (.env) — ver .env.example para los valores de XAMPP
# --------------------------------------------------------------------------


def env(key, default=None, cast=str):
    value = os.environ.get(key, default)
    if value is None:
        return value
    if cast is bool:
        return str(value).lower() in ("1", "true", "yes", "on")
    return cast(value)


# Carga sencilla de un archivo .env sin dependencias externas
_env_path = BASE_DIR / ".env"
if _env_path.exists():
    for _line in _env_path.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if not _line or _line.startswith("#") or "=" not in _line:
            continue
        _key, _value = _line.split("=", 1)
        os.environ.setdefault(_key.strip(), _value.strip())

SECRET_KEY = env("DJANGO_SECRET_KEY", "django-insecure-cambiar-esta-clave-en-produccion")
DEBUG = env("DJANGO_DEBUG", "True", cast=bool)
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")

# --------------------------------------------------------------------------
# Aplicaciones (cada app = un módulo funcional del plan de tesis)
# --------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    # apps del sistema (capa de dominio / modelo)
    "cuentas.apps.CuentasConfig",
    "catalogos.apps.CatalogosConfig",
    "bienes.apps.BienesConfig",
    "asignaciones.apps.AsignacionesConfig",
    "desplazamientos.apps.DesplazamientosConfig",
    "conservacion.apps.ConservacionConfig",
    "inventario.apps.InventarioConfig",
    "bajas.apps.BajasConfig",
    "auditoria.apps.AuditoriaConfig",
    "dashboard.apps.DashboardConfig",
    "reportes.apps.ReportesConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "auditoria.middleware.RegistroAccesoMiddleware",  # RF05 / RNF12
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --------------------------------------------------------------------------
# Base de datos — MySQL servido por XAMPP (por defecto host=127.0.0.1 puerto 3306,
# usuario root sin contraseña). Ajusta el archivo .env si tu XAMPP usa otra
# configuración.
# --------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": env("DB_NAME", "sigepat_bd"),
        "USER": env("DB_USER", "root"),
        "PASSWORD": env("DB_PASSWORD", ""),
        "HOST": env("DB_HOST", "127.0.0.1"),
        "PORT": env("DB_PORT", "3306"),
        "OPTIONS": {
            "charset": "utf8mb4",
        },
    }
}

AUTH_USER_MODEL = "cuentas.Usuario"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-pe"
TIME_ZONE = "America/Lima"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "cuentas:login"
LOGIN_REDIRECT_URL = "dashboard:panel"
LOGOUT_REDIRECT_URL = "cuentas:login"

# RNF04: el buscador debe responder en poco tiempo -> paginación por defecto
PAGINATE_BY = 20
