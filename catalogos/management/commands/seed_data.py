"""
Comando de siembra de datos de prueba para SIGEPAT.

- Los catálogos (Rol, UnidadOrganica, CategoriaBien, CausalBaja) mantienen su
  dominio real y finito, tal como se acordó con el usuario.
- Las tablas principales / transaccionales se siembran con ~100 registros
  (o más) cada una, respetando la integridad referencial.

Uso:
    python manage.py seed_data            # siembra (agrega) datos
    python manage.py seed_data --reset    # borra datos previos del dominio y vuelve a sembrar
"""
import random
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.hashers import make_password
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from faker import Faker

fake = Faker("es_ES")

# Un PDF mínimo válido (una página en blanco) usado como contenido de
# ejemplo para los documentos de respaldo sembrados.
PDF_DUMMY = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\n"
    b"xref\n0 4\ntrailer<</Size 4/Root 1 0 R>>\n%%EOF"
)

UNIDADES = [
    ("Alcaldía", "ALC"), ("Gerencia Municipal", "GM"), ("Secretaría General", "SG"),
    ("Unidad de Control Patrimonial", "UCP"), ("Unidad de Abastecimiento", "UA"),
    ("Unidad de Contabilidad", "CONT"), ("Unidad de Tesorería", "TES"),
    ("Unidad de Recursos Humanos", "RRHH"), ("Oficina de Planeamiento y Presupuesto", "OPP"),
    ("Oficina de Infraestructura", "OINF"), ("Oficina de Desarrollo Social", "ODS"),
    ("Oficina de Desarrollo Económico Local", "ODEL"), ("Unidad de Tecnologías de la Información", "UTI"),
    ("Registro Civil", "RRCC"), ("Almacén Central", "ALM"),
]

CATEGORIAS = [
    ("Mobiliario de oficina", 8), ("Equipos de cómputo", 4), ("Equipos de comunicación", 5),
    ("Vehículos", 7), ("Herramientas", 5), ("Equipos audiovisuales", 5), ("Electrodomésticos", 6),
    ("Equipos médicos", 6), ("Maquinaria", 10), ("Equipos de seguridad", 5),
    ("Instrumentos de medición", 5), ("Mobiliario educativo", 8), ("Equipos de cocina", 5),
    ("Equipos deportivos", 5), ("Otros bienes", 4),
]

CAUSALES_BAJA = [
    "Obsolescencia técnica", "Deterioro por uso", "Pérdida", "Hurto", "Robo",
    "Siniestro", "Reposición por garantía", "Donación a terceros",
]

ROLES = [
    ("ADMINISTRADOR", "Administrador del sistema"),
    ("CONTROL_PATRIMONIAL", "Personal de Control Patrimonial"),
    ("ALMACEN", "Personal de Almacén"),
    ("CONTABILIDAD", "Personal de Contabilidad"),
    ("RESPONSABLE", "Servidor / usuario responsable de bienes"),
    ("JEFATURA", "Jefatura de la Unidad de Control Patrimonial"),
]

random.seed(42)
fake.seed_instance(42)


class Command(BaseCommand):
    help = "Siembra datos de prueba (catálogos reales + ~100 registros por tabla principal) en MySQL."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Elimina los datos previos antes de sembrar.")

    def handle(self, *args, **options):
        from asignaciones.models import Asignacion
        from auditoria.models import LogAuditoria
        from bajas.models import Baja, Saneamiento
        from bienes.models import Bien, DocumentoRespaldo, HistorialCambioBien
        from catalogos.models import CategoriaBien, CausalBaja, Rol, UnidadOrganica
        from conservacion.models import RegistroConservacion
        from cuentas.models import RegistroAcceso, Usuario
        from desplazamientos.models import Desplazamiento
        from inventario.models import Inventario, VerificacionInventario

        if options["reset"]:
            self.stdout.write("Eliminando datos previos...")
            for modelo in [
                LogAuditoria, RegistroAcceso, Saneamiento, VerificacionInventario, Inventario,
                Baja, Desplazamiento, RegistroConservacion, HistorialCambioBien, DocumentoRespaldo,
                Asignacion, Bien,
            ]:
                modelo.objects.all().delete()
            Usuario.objects.filter(is_superuser=False).delete()

        with transaction.atomic():
            roles = self._sembrar_roles(Rol)
            unidades = self._sembrar_unidades(UnidadOrganica)
            categorias = self._sembrar_categorias(CategoriaBien)
            causales = self._sembrar_causales(CausalBaja)
            usuarios = self._sembrar_usuarios(Usuario, roles, unidades)

        with transaction.atomic():
            bienes = self._sembrar_bienes(Bien, categorias, unidades, usuarios)

        with transaction.atomic():
            self._sembrar_documentos(DocumentoRespaldo, bienes, usuarios)
            self._sembrar_historial(HistorialCambioBien, bienes, usuarios)
            self._sembrar_asignaciones(Asignacion, bienes, usuarios)
            self._sembrar_desplazamientos(Desplazamiento, bienes, usuarios)
            self._sembrar_conservacion(RegistroConservacion, bienes, usuarios)

        with transaction.atomic():
            inventarios = self._sembrar_inventarios(Inventario, unidades, usuarios)
            verificaciones = self._sembrar_verificaciones(VerificacionInventario, inventarios, usuarios)

        with transaction.atomic():
            self._sembrar_bajas(Baja, bienes, causales, usuarios)
            self._sembrar_saneamientos(Saneamiento, verificaciones)
            self._sembrar_accesos(RegistroAcceso, usuarios)
            self._sembrar_auditoria(LogAuditoria, usuarios, bienes)

        self.stdout.write(self.style.SUCCESS("Siembra de datos completada."))
        self._reporte_conteos()

    # ------------------------------------------------------------------
    # Catálogos (dominio real, finito)
    # ------------------------------------------------------------------
    def _sembrar_roles(self, Rol):
        roles = {}
        for codigo, nombre in ROLES:
            rol, _ = Rol.objects.get_or_create(codigo=codigo, defaults={"nombre": nombre})
            roles[codigo] = rol
        self.stdout.write(f"Roles: {Rol.objects.count()}")
        return roles

    def _sembrar_unidades(self, UnidadOrganica):
        unidades = []
        for nombre, siglas in UNIDADES:
            unidad, _ = UnidadOrganica.objects.get_or_create(nombre=nombre, defaults={"siglas": siglas})
            unidades.append(unidad)
        self.stdout.write(f"Unidades orgánicas: {UnidadOrganica.objects.count()}")
        return unidades

    def _sembrar_categorias(self, CategoriaBien):
        categorias = []
        for nombre, vida_util in CATEGORIAS:
            categoria, _ = CategoriaBien.objects.get_or_create(nombre=nombre, defaults={"vida_util_anios": vida_util})
            categorias.append(categoria)
        self.stdout.write(f"Categorías de bienes: {CategoriaBien.objects.count()}")
        return categorias

    def _sembrar_causales(self, CausalBaja):
        causales = []
        for nombre in CAUSALES_BAJA:
            causal, _ = CausalBaja.objects.get_or_create(nombre=nombre)
            causales.append(causal)
        self.stdout.write(f"Causales de baja: {CausalBaja.objects.count()}")
        return causales

    # ------------------------------------------------------------------
    # Tablas principales (~100 o más registros)
    # ------------------------------------------------------------------
    def _sembrar_usuarios(self, Usuario, roles, unidades):
        if not Usuario.objects.filter(is_superuser=True).exists():
            Usuario.objects.create_superuser(
                username="admin", email="admin@sigepat.local", password="Admin12345",
                first_name="Administrador", last_name="SIGEPAT", rol=roles["ADMINISTRADOR"],
            )

        pesos_roles = ["RESPONSABLE"] * 55 + ["CONTROL_PATRIMONIAL"] * 20 + ["ALMACEN"] * 10 \
            + ["CONTABILIDAD"] * 8 + ["JEFATURA"] * 4 + ["ADMINISTRADOR"] * 3
        usuarios = list(Usuario.objects.exclude(is_superuser=True))
        objetivo = 100
        contador = len(usuarios)
        password_hash = make_password("Usuario2026")
        nuevos = []
        while contador < objetivo:
            nombre = fake.first_name()
            apellido = fake.last_name()
            username = f"{nombre}.{apellido}{contador}".lower().replace(" ", "")
            if Usuario.objects.filter(username=username).exists():
                contador += 1
                continue
            usuario = Usuario(
                username=username, first_name=nombre, last_name=apellido,
                email=f"{username}@unionashaninka.gob.pe",
                dni=str(fake.random_number(digits=8, fix_len=True)),
                telefono=fake.phone_number()[:20],
                rol=roles[random.choice(pesos_roles)],
                unidad_organica=random.choice(unidades),
                is_active=random.random() > 0.05,
                password=password_hash,
            )
            nuevos.append(usuario)
            contador += 1
        Usuario.objects.bulk_create(nuevos)
        usuarios = list(Usuario.objects.exclude(is_superuser=True))
        self.stdout.write(f"Usuarios: {Usuario.objects.count()}")
        return usuarios

    def _sembrar_bienes(self, Bien, categorias, unidades, usuarios):
        denominaciones = [
            "Escritorio de melamine", "Silla giratoria", "Computadora de escritorio", "Laptop",
            "Impresora multifuncional", "Proyector multimedia", "Camioneta pick-up", "Motocicleta lineal",
            "Radio portátil", "Extintor PQS", "Ventilador de pie", "Refrigeradora", "Microondas",
            "Cámara fotográfica digital", "Escalera de aluminio", "Taladro percutor", "Motosierra",
            "Estabilizador de voltaje", "Archivador metálico", "Pizarra acrílica", "Mesa de reuniones",
            "Ecógrafo portátil", "Tensiómetro digital", "GPS portátil", "Cámara de videovigilancia",
            "Generador eléctrico", "Compresora de aire", "Cortadora de césped", "Router inalámbrico",
            "Switch de red", "UPS de 1000VA", "Escritorio gerencial", "Pupitre escolar",
        ]
        objetivo_activos = 120
        objetivo_baja = 100
        bienes = []
        hoy = date.today()

        def crear_bien(situacion_final):
            categoria = random.choice(categorias)
            fecha_alta = fake.date_between(start_date=date(2019, 1, 1), end_date=hoy - timedelta(days=30))
            bien = Bien(
                denominacion=random.choice(denominaciones),
                marca=fake.company()[:80],
                modelo=fake.bothify(text="MOD-####"),
                serie=fake.bothify(text="SN-????-######").upper(),
                categoria=categoria,
                unidad_organica=random.choice(unidades),
                valor_adquisicion=Decimal(random.randrange(150, 45000)) / Decimal(1),
                fecha_alta=fecha_alta,
                tipo_adquisicion=random.choice([c[0] for c in Bien.TIPO_ADQUISICION]),
                descripcion=fake.sentence(nb_words=10),
                creado_por=random.choice(usuarios),
                situacion=situacion_final,
            )
            bien.save()  # genera codigo_patrimonial automáticamente (RF07)
            return bien

        for _ in range(objetivo_activos):
            bienes.append(crear_bien("ACTIVO"))
        for _ in range(objetivo_baja):
            bien = crear_bien("BAJA")
            bienes.append(bien)

        self.stdout.write(f"Bienes patrimoniales: {Bien.objects.count()}")
        return bienes

    def _sembrar_documentos(self, DocumentoRespaldo, bienes, usuarios):
        tipos = [t[0] for t in DocumentoRespaldo.TIPOS]
        creados = 0
        for bien in bienes:
            cantidad = random.choice([1, 1, 2])
            for _ in range(cantidad):
                doc = DocumentoRespaldo(
                    bien=bien, tipo_documento=random.choice(tipos),
                    descripcion=fake.sentence(nb_words=6),
                    cargado_por=random.choice(usuarios),
                )
                doc.archivo.save(f"{bien.codigo_patrimonial}_{creados}.pdf", ContentFile(PDF_DUMMY), save=False)
                doc.save()
                creados += 1
        self.stdout.write(f"Documentos de respaldo: {DocumentoRespaldo.objects.count()}")

    def _sembrar_historial(self, HistorialCambioBien, bienes, usuarios):
        campos = ["denominacion", "valor_adquisicion", "unidad_organica", "descripcion"]
        registros = []
        for _ in range(150):
            bien = random.choice(bienes)
            campo = random.choice(campos)
            registros.append(HistorialCambioBien(
                bien=bien, campo_modificado=campo,
                valor_anterior=fake.word(), valor_nuevo=fake.word(),
                usuario=random.choice(usuarios),
            ))
        HistorialCambioBien.objects.bulk_create(registros)
        self.stdout.write(f"Historial de cambios: {HistorialCambioBien.objects.count()}")

    def _sembrar_asignaciones(self, Asignacion, bienes, usuarios):
        activos = [b for b in bienes if b.situacion == "ACTIVO"]
        contador = Asignacion.objects.count()
        for bien in activos:
            fecha = fake.date_between(start_date=bien.fecha_alta, end_date=date.today())
            asignacion = Asignacion(
                bien=bien, responsable=random.choice(usuarios), fecha_asignacion=fecha,
                observaciones=fake.sentence(nb_words=6), asignado_por=random.choice(usuarios), activa=True,
            )
            asignacion.save()
            contador += 1
            if random.random() < 0.25:
                # historial de reasignación: cierra la anterior y crea una nueva vigente
                fecha_fin = fecha + timedelta(days=random.randint(30, 400))
                if fecha_fin < date.today():
                    asignacion.cerrar(fecha_fin)
                    nueva = Asignacion(
                        bien=bien, responsable=random.choice(usuarios), fecha_asignacion=fecha_fin,
                        observaciones="Reasignación", asignado_por=random.choice(usuarios), activa=True,
                    )
                    nueva.save()
        self.stdout.write(f"Asignaciones: {Asignacion.objects.count()}")

    # RF14-RF17: destinos reales de desplazamiento externo (centros poblados /
    # localidades del ámbito de la Municipalidad Distrital de Unión Asháninka,
    # VRAEM), en vez de ciudades genéricas generadas por Faker (que no
    # corresponden a la zona real de operación).
    DESTINOS_REALES = [
        "Santa Rosa", "Tambo", "Pichari", "Llochegua", "Canayre", "Ccatun Rumi",
        "Omaya", "Santa Rosa Baja", "Sivia", "Otari", "Tarancato", "Puerto Mayo",
        "San Miguel", "Anco", "Anchihuay", "Rio Magdalena", "Ayna", "Chilcas",
        "Chungui", "Chuvivana", "Ninabamba", "Samugari",
    ]

    def _sembrar_desplazamientos(self, Desplazamiento, bienes, usuarios):
        estados = ["APROBADO"] * 6 + ["PENDIENTE"] * 2 + ["RECHAZADO"] * 2
        registros = []
        for _ in range(150):
            bien = random.choice(bienes)
            estado = random.choice(estados)
            fecha_solicitud = timezone.make_aware(
                fake.date_time_between(start_date=date(2023, 1, 1), end_date="now")
            )
            desplazamiento = Desplazamiento(
                bien=bien, solicitante=random.choice(usuarios),
                tipo=random.choice(["INTERNO", "EXTERNO"]),
                origen=str(bien.unidad_organica), destino=random.choice(self.DESTINOS_REALES),
                motivo=fake.sentence(nb_words=8), estado=estado,
                fecha_solicitud=fecha_solicitud,
            )
            if estado != "PENDIENTE":
                desplazamiento.autorizado_por = random.choice(usuarios)
                desplazamiento.fecha_resolucion = fecha_solicitud + timedelta(days=random.randint(1, 5))
            registros.append(desplazamiento)
        Desplazamiento.objects.bulk_create(registros)
        self.stdout.write(f"Desplazamientos: {Desplazamiento.objects.count()}")

    def _sembrar_conservacion(self, RegistroConservacion, bienes, usuarios):
        estados = [e[0] for e in RegistroConservacion.ESTADOS]
        pesos = ["BUENO"] * 5 + ["REGULAR"] * 3 + ["NUEVO"] * 2 + ["MALO"] * 2 + ["CHATARRA"]
        registros = []
        for bien in bienes:
            for _ in range(random.choice([1, 1, 2])):
                registros.append(RegistroConservacion(
                    bien=bien, estado=random.choice(pesos),
                    observaciones=fake.sentence(nb_words=6),
                    registrado_por=random.choice(usuarios),
                ))
        RegistroConservacion.objects.bulk_create(registros)
        self.stdout.write(f"Registros de conservación: {RegistroConservacion.objects.count()}")

    def _sembrar_inventarios(self, Inventario, unidades, usuarios):
        responsables = [u for u in usuarios if u.rol and u.rol.codigo in ("CONTROL_PATRIMONIAL", "ADMINISTRADOR")] or usuarios
        anios = list(range(2019, 2026))
        combos = [(a, u) for a in anios for u in unidades]
        random.shuffle(combos)
        combos = combos[:100]
        inventarios = []
        for anio, unidad in combos:
            fecha_inicio = date(anio, random.randint(9, 11), random.randint(1, 28))
            cerrado = anio < 2026 or random.random() < 0.5
            inv = Inventario(
                anio=anio, unidad_organica=unidad, fecha_inicio=fecha_inicio,
                responsable=random.choice(responsables),
                estado="CERRADO" if cerrado else "EN_PROCESO",
                conciliado_contabilidad=cerrado,
            )
            if cerrado:
                inv.fecha_cierre = fecha_inicio + timedelta(days=random.randint(10, 45))
                inv.observaciones_cierre = "Cierre generado en la siembra de datos de prueba."
            inv.save()
            inventarios.append(inv)
        self.stdout.write(f"Inventarios físicos: {Inventario.objects.count()}")
        return inventarios

    def _sembrar_verificaciones(self, VerificacionInventario, inventarios, usuarios):
        """RF21-RF24: siembra de verificaciones, reconciliadas con `bienes_esperados`.

        Un inventario `CERRADO` debe quedar cuadrado: esperados = verificados +
        faltantes (más los sobrantes, que son hallazgos fuera del universo
        esperado). Antes solo se verificaba una muestra aleatoria de 2-6 bienes
        por inventario y se marcaba CERRADO igual, dejando la mayoría de los
        bienes esperados sin ninguna verificación asociada — el acta mostraba,
        p. ej., "Bienes esperados: 13" pero solo 6-7 filas en la tabla, sin
        explicación. Para un inventario `EN_PROCESO` sí se deja una muestra
        parcial (todavía no se ha verificado todo, lo cual es realista).
        """
        from bienes.models import Bien

        verificaciones = []
        for inv in inventarios:
            # Mismo filtro que la propiedad `bienes_esperados` del modelo, para
            # que la siembra sea coherente con lo que el acta va a mostrar.
            bienes_unidad = list(Bien.objects.filter(unidad_organica=inv.unidad_organica, situacion="ACTIVO"))
            if not bienes_unidad:
                continue

            if inv.estado == "CERRADO":
                # Inventario cerrado: se verifica el 100% del universo esperado,
                # igual que exige `CerrarInventarioView.post()` en la app real
                # (todo bien esperado sin verificación explícita se marca
                # FALTANTE antes de poder cerrar el inventario).
                por_verificar = bienes_unidad
            else:
                # Inventario en proceso: solo una muestra parcial verificada hasta ahora.
                por_verificar = random.sample(bienes_unidad, k=min(len(bienes_unidad), random.randint(2, 6)))

            for bien in por_verificar:
                resultado = random.choices(["ENCONTRADO", "FALTANTE"], weights=[78, 22])[0]
                verificaciones.append(VerificacionInventario(
                    inventario=inv,
                    bien=bien,
                    resultado=resultado,
                    ubicacion_encontrada=str(inv.unidad_organica),
                    estado_conservacion_encontrado=random.choice(["BUENO", "REGULAR", "MALO"]),
                    verificado_por=random.choice(usuarios),
                    origen_dispositivo=random.choice(["WEB", "MOVIL"]),
                ))
            if random.random() < 0.55:
                verificaciones.append(VerificacionInventario(
                    inventario=inv, bien=None,
                    descripcion_hallazgo=f"Bien no registrado hallado en {inv.unidad_organica}",
                    resultado="SOBRANTE",
                    ubicacion_encontrada=str(inv.unidad_organica),
                    estado_conservacion_encontrado=random.choice(["BUENO", "REGULAR"]),
                    verificado_por=random.choice(usuarios),
                    origen_dispositivo=random.choice(["WEB", "MOVIL"]),
                ))
        VerificacionInventario.objects.bulk_create(verificaciones)
        todas = list(VerificacionInventario.objects.all())
        self.stdout.write(f"Verificaciones de inventario: {VerificacionInventario.objects.count()}")
        return todas

    def _sembrar_bajas(self, Baja, bienes, causales, usuarios):
        disposiciones = [d[0] for d in Baja._meta.get_field("disposicion_final").choices]
        registros = []
        for bien in bienes:
            if bien.situacion != "BAJA":
                continue
            registros.append(Baja(
                bien=bien, causal=random.choice(causales),
                fecha_baja=fake.date_between(start_date=bien.fecha_alta, end_date=date.today()),
                disposicion_final=random.choice(disposiciones),
                observaciones=fake.sentence(nb_words=8),
                registrado_por=random.choice(usuarios),
            ))
        Baja.objects.bulk_create(registros)
        self.stdout.write(f"Bajas registradas: {Baja.objects.count()}")

    def _sembrar_saneamientos(self, Saneamiento, verificaciones):
        candidatas = [v for v in verificaciones if v.resultado in ("SOBRANTE", "FALTANTE")]
        estados = [e[0] for e in Saneamiento.ESTADO_TRAMITE]
        registros = []
        for verificacion in candidatas:
            fecha_inicio = verificacion.fecha_verificacion.date() if verificacion.fecha_verificacion else date.today()
            estado = random.choice(estados)
            saneamiento = Saneamiento(
                verificacion=verificacion, tipo=verificacion.resultado,
                estado_tramite=estado, plazo_normativo_dias=random.choice([30, 45, 60]),
                fecha_inicio_tramite=fecha_inicio,
                observaciones=fake.sentence(nb_words=6),
            )
            if estado == "CONCLUIDO":
                saneamiento.fecha_resolucion = fecha_inicio + timedelta(days=random.randint(10, 60))
            registros.append(saneamiento)
        Saneamiento.objects.bulk_create(registros)
        self.stdout.write(f"Saneamientos: {Saneamiento.objects.count()}")

    def _sembrar_accesos(self, RegistroAcceso, usuarios):
        registros = []
        for _ in range(150):
            usuario = random.choice(usuarios)
            exitoso = random.random() > 0.15
            registros.append(RegistroAcceso(
                usuario=usuario if exitoso else None,
                username_ingresado=usuario.username,
                exitoso=exitoso,
                direccion_ip=fake.ipv4(),
            ))
        RegistroAcceso.objects.bulk_create(registros)
        self.stdout.write(f"Registros de acceso: {RegistroAcceso.objects.count()}")

    def _sembrar_auditoria(self, LogAuditoria, usuarios, bienes):
        acciones = [a[0] for a in LogAuditoria.ACCIONES]
        registros = []
        for _ in range(150):
            bien = random.choice(bienes)
            registros.append(LogAuditoria(
                usuario=random.choice(usuarios), accion=random.choice(acciones),
                modelo_afectado="Bien", objeto_id=str(bien.pk),
                detalle=f"Operación sobre {bien.codigo_patrimonial}",
            ))
        LogAuditoria.objects.bulk_create(registros)
        self.stdout.write(f"Registros de auditoría: {LogAuditoria.objects.count()}")

    def _reporte_conteos(self):
        from asignaciones.models import Asignacion
        from auditoria.models import LogAuditoria
        from bajas.models import Baja, Saneamiento
        from bienes.models import Bien, DocumentoRespaldo, HistorialCambioBien
        from catalogos.models import CategoriaBien, CausalBaja, Rol, UnidadOrganica
        from conservacion.models import RegistroConservacion
        from cuentas.models import RegistroAcceso, Usuario
        from desplazamientos.models import Desplazamiento
        from inventario.models import Inventario, VerificacionInventario

        modelos = [
            Rol, UnidadOrganica, CategoriaBien, CausalBaja, Usuario, Bien, DocumentoRespaldo,
            HistorialCambioBien, Asignacion, Desplazamiento, RegistroConservacion, Inventario,
            VerificacionInventario, Baja, Saneamiento, RegistroAcceso, LogAuditoria,
        ]
        self.stdout.write("\nResumen final de registros por tabla:")
        for modelo in modelos:
            self.stdout.write(f"  {modelo._meta.verbose_name_plural}: {modelo.objects.count()}")
