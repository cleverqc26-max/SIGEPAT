# SIGEPAT — Sistema de Gestión y Control de Bienes Patrimoniales

Municipalidad Distrital de Unión Asháninka, 2026
Plan de tesis: *"Desarrollo de un sistema web para la gestión y control de bienes
patrimoniales y evaluación de su calidad según la norma ISO/IEC 25010..."*

Este proyecto implementa **todos los requisitos funcionales (RF01–RF31) y no
funcionales (RNF01–RNF16)** definidos en el documento
`Requisitos_RF_RNF_HU_SistemaBienesPatrimoniales_V_OK.docx`, desarrollado con
**Python + Django** (patrón MVT, la variante Django del MVC) y **MySQL** como
motor relacional, siguiendo la metodología ágil **XP (Programación Extrema)**
del plan de tesis.

---

## 1. ¿Por qué Django y no Flask?

| Necesidad del sistema | Django | Flask |
|---|---|---|
| ORM + migraciones | Incluido | Requiere SQLAlchemy + Flask-Migrate |
| Autenticación, sesiones, hash de contraseñas (RNF11) | Incluido | Requiere Flask-Login + configuración manual |
| Roles y permisos (RF03-RF04) | Se modela con el ORM + mixins | Se arma a mano |
| Panel de administración (para operar catálogos rápido) | Incluido (`/admin/`) | Requiere Flask-Admin |
| Patrón MVC | MVT (Modelo–Vista–Plantilla), equivalente directo | No trae un patrón definido |
| Velocidad de desarrollo para un CRUD-heavy system con cronograma XP ajustado | Alta | Media/baja (hay que ensamblar piezas) |

Flask es preferible para microservicios o APIs muy pequeñas; este sistema
tiene múltiples módulos con formularios, permisos y reportes, escenario en el
que Django reduce tiempo de desarrollo y riesgo técnico.

### Arquitectura MVC/MVT del proyecto

```
Modelo (Model)      -> <app>/models.py      (tablas MySQL, reglas de negocio)
Vista/Controlador   -> <app>/views.py       (lógica de la aplicación)
Plantilla (View)    -> templates/<app>/*.html (presentación, Bootstrap 5)
```

Cada módulo del plan de tesis es una **app Django independiente** (capa por
módulo, RNF15 — mantenibilidad):

| App | Módulo del plan de tesis | Requisitos cubiertos |
|---|---|---|
| `cuentas` | Gestión de usuarios y accesos | RF01–RF05 |
| `bienes` | Registro y codificación de bienes | RF06–RF10 |
| `asignaciones` | Asignación en uso y responsables | RF11–RF13 |
| `desplazamientos` | Control de desplazamientos | RF14–RF17 |
| `conservacion` | Estado de conservación | RF18–RF19 |
| `inventario` | Inventario físico | RF20–RF24 |
| `bajas` | Altas, bajas y saneamiento | RF25–RF27 |
| `reportes` | Reportes y formatos normativos | RF28–RF30 |
| `dashboard` | Panel de indicadores | RF31 |
| `auditoria` | Trazabilidad de operaciones críticas | RNF12 |
| `catalogos` | Tablas de dominio (roles, unidades, categorías, causales) | soporte |

Los requisitos no funcionales están implementados así:

- **RNF01-RNF04 (eficiencia):** paginación en listados, búsqueda por índice
  (`codigo_patrimonial` es `unique`), agregaciones SQL (no bucles en Python)
  en el dashboard, imágenes/documentos servidos como archivos estáticos.
- **RNF05-RNF08 (usabilidad):** interfaz uniforme Bootstrap 5, mensajes de
  validación en español, diseño responsive (`meta viewport` + grid de
  Bootstrap), textos de ayuda en los formularios más complejos.
- **RNF09-RNF10 (soporte a adecuación funcional):** ver carpeta `tests/`
  (crear casos de prueba por RF durante el desarrollo XP) y validaciones de
  reglas de negocio en `forms.py`/`models.py` (p. ej. no se puede dar de baja
  sin causal válida).
- **RNF11-RNF12 (seguridad):** contraseñas cifradas por Django
  (`PBKDF2`), sesión validada en cada vista (`LoginRequiredMixin`), log de
  auditoría (`auditoria.LogAuditoria`) y de accesos (`cuentas.RegistroAcceso`).
- **RNF13 (fiabilidad):** ver sección "Respaldo de la base de datos" más abajo.
- **RNF14 (compatibilidad):** Bootstrap 5 + JS estándar, compatible con
  Chrome/Firefox/Edge actuales.
- **RNF15 (mantenibilidad):** una app Django por módulo, con su propio
  `models.py`/`views.py`/`urls.py`.
- **RNF16 (portabilidad):** configuración por variables de entorno (`.env`),
  sin rutas ni credenciales fijas en el código.

---

## 2. Requisitos previos

- **XAMPP** (con MySQL/MariaDB activo) — https://www.apachefriends.org/
- **Python 3.11 o superior** — https://www.python.org/downloads/ (marcar
  "Add Python to PATH" al instalar en Windows)
- **Visual Studio Code** con la extensión **Python** (Microsoft)
- Git (opcional, solo si vas a versionar el proyecto)

> **Nota sobre versiones:** `requirements.txt` fija **Django 4.2 (LTS)** en
> vez de la serie 5.x. Django 5 exige MariaDB 10.5+, y la mayoría de
> instalaciones de XAMPP traen MariaDB 10.4.x — con Django 5 el `migrate`
> falla con `NotSupportedError: MariaDB 10.5 or later is required`. Django
> 4.2 es una versión LTS (soporte extendido) y se verificó que el proyecto
> corre igual en ambas series, sin cambios de código. Si tu XAMPP ya trae
> MariaDB 10.5+ o MySQL 8+, puedes usar `Django>=5,<6` sin problema.

---

## 3. Preparar la base de datos en XAMPP

1. Abre el **Panel de Control de XAMPP** y da clic en **Start** en el módulo
   **MySQL** (no hace falta iniciar Apache; Django trae su propio servidor).
2. Abre **phpMyAdmin** (botón "Admin" del módulo MySQL, o
   `http://localhost/phpmyadmin`).
3. Crea una base de datos nueva llamada **`sigepat_bd`** con cotejamiento
   `utf8mb4_unicode_ci`.
4. XAMPP trae por defecto el usuario `root` **sin contraseña**, lo cual ya
   coincide con la configuración por defecto del proyecto (ver `.env.example`).
   Si tu instalación de XAMPP tiene una contraseña distinta para `root`,
   anótala: la usarás en el paso 4.2.

---

## 4. Configurar y ejecutar el proyecto en Visual Studio Code

### 4.1 Abrir el proyecto

Descomprime el archivo entregado y abre la carpeta `sigepat/` con
**Archivo → Abrir carpeta...** en VS Code.

### 4.2 Crear el entorno virtual e instalar dependencias

Abre una terminal integrada en VS Code (**Terminal → Nueva terminal**) y
ejecuta:

```bash
# Windows (PowerShell o cmd)
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Cuando VS Code pregunte "¿Quieres usar este entorno para el workspace?",
selecciona **Sí** (o elige el intérprete `venv` manualmente con
`Ctrl+Shift+P` → *Python: Select Interpreter*).

### 4.3 Configurar la conexión a MySQL

Copia `.env.example` como `.env` (mismo directorio) y ajusta solo si tu
XAMPP usa credenciales distintas a las de por defecto:

```
DB_NAME=sigepat_bd
DB_USER=root
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=3306
```

### 4.4 Migrar el esquema y sembrar datos de prueba

Con el entorno virtual activado:

```bash
python manage.py migrate
python manage.py seed_data
```

`seed_data` crea:

- Los catálogos con su dominio real (6 roles, 15 unidades orgánicas, 15
  categorías de bienes, 8 causales de baja: no tiene sentido "inflar" estas
  tablas a 100 filas porque su universo real es ese).
- **~100 o más registros de prueba en cada tabla principal**: usuarios,
  bienes, documentos de respaldo, historial de cambios, asignaciones,
  desplazamientos, registros de conservación, inventarios, verificaciones de
  inventario, bajas, saneamientos, registros de acceso y auditoría.
- Un usuario **administrador**: `admin` / `Admin12345`
- El resto de usuarios de prueba usan la contraseña `Usuario2026` (el nombre
  de usuario se muestra en el listado de `/cuentas/usuarios/` ya autenticado
  como admin).

Si necesitas volver a sembrar desde cero (por ejemplo, tras cambiar algo):

```bash
python manage.py seed_data --reset
```

### 4.5 Ejecutar el servidor

```bash
python manage.py runserver
```

Abre `http://127.0.0.1:8000/` en tu navegador — te redirige al login.
Ingresa con `admin` / `Admin12345`.

También puedes ejecutar/depurar con **F5** en VS Code: el proyecto incluye
`.vscode/launch.json` ya configurado ("Django: runserver").

### 4.6 Panel de administración

`http://127.0.0.1:8000/admin/` — útil para revisar/editar cualquier tabla
directamente durante el desarrollo (usa las mismas credenciales de `admin`).

---

## 5. Recorrido rápido por los módulos

| Ruta | Módulo |
|---|---|
| `/dashboard/` | Panel general (RF31) |
| `/bienes/` | Registro, búsqueda y ficha de bienes (RF06-RF10) |
| `/asignaciones/` | Asignar/reasignar bienes (RF11-RF13) |
| `/desplazamientos/` | Solicitar y aprobar desplazamientos (RF14-RF17) |
| `/inventario/` | Abrir, verificar y cerrar inventarios físicos (RF20-RF24) |
| `/bajas/` | Bajas y saneamiento administrativo (RF25-RF27) |
| `/reportes/` | Reportes filtrables + exportación PDF/Excel (RF28-RF30) |
| `/cuentas/usuarios/` | Administración de usuarios (solo rol Administrador) |

Cada ficha de bien (`/bienes/<id>/`) centraliza las acciones: adjuntar
documentos, asignar, solicitar desplazamiento, registrar estado de
conservación y dar de baja.

---

## 6. Respaldo de la base de datos (RNF13)

XAMPP incluye `mysqldump`. Ejemplo de respaldo manual (ajusta la ruta al
`bin` de tu instalación de XAMPP):

```bash
"C:\xampp\mysql\bin\mysqldump" -u root sigepat_bd > respaldo_sigepat.sql
```

Para un entorno productivo real se recomienda automatizar este comando con
el Programador de tareas de Windows (o `cron` en Linux) según la política de
respaldo de la entidad.

---

## 7. Estructura del proyecto

```
sigepat/
├── config/                # settings.py, urls.py (proyecto Django)
├── cuentas/                # RF01-RF05
├── catalogos/              # catálogos + comando seed_data
├── bienes/                 # RF06-RF10
├── asignaciones/            # RF11-RF13
├── desplazamientos/        # RF14-RF17
├── conservacion/            # RF18-RF19
├── inventario/              # RF20-RF24
├── bajas/                    # RF25-RF27
├── auditoria/               # RNF12 (log + middleware de accesos)
├── dashboard/               # RF31
├── reportes/                 # RF28-RF30 (exportadores PDF/Excel)
├── templates/                # Plantillas Bootstrap 5 (una carpeta por app)
├── static/                    # Archivos estáticos propios (vacío por defecto)
├── requirements.txt
├── .env.example
└── manage.py
```

---

## 8. Notas para la sustentación

- El código fue **migrado y poblado contra una base de datos MySQL real**
  durante su elaboración (no solo contra SQLite), para verificar que el
  esquema y las consultas son válidos en el motor que exige la tesis.
- Los flujos críticos (alta de bien con generación automática de código,
  asignación/reasignación, solicitud y aprobación de desplazamiento,
  apertura/verificación/cierre de inventario con generación automática de
  sobrantes y faltantes, y registro de baja) fueron probados de extremo a
  extremo antes de la entrega.
- Los documentos de respaldo sembrados por `seed_data` son archivos PDF de
  marcador de posición (para no depender de archivos reales); en producción
  el usuario adjunta sus propios documentos desde el formulario del bien.
