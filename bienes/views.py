from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from auditoria.models import registrar_auditoria
from catalogos.models import Rol
from cuentas.mixins import RolRequeridoMixin

from .forms import BienForm, DocumentoRespaldoForm
from .models import Bien, DocumentoRespaldo, HistorialCambioBien

ROLES_GESTION_BIENES = (Rol.CONTROL_PATRIMONIAL, Rol.ADMINISTRADOR)


class ListaBienesView(LoginRequiredMixin, ListView):
    """RF10 / RNF03: búsqueda y filtrado de bienes."""

    model = Bien
    template_name = "bienes/lista.html"
    context_object_name = "bienes"
    paginate_by = 20

    def get_queryset(self):
        qs = Bien.objects.select_related("categoria", "unidad_organica").order_by("-fecha_registro")
        q = self.request.GET.get("q")
        unidad = self.request.GET.get("unidad_organica")
        situacion = self.request.GET.get("situacion")
        if q:
            qs = qs.filter(models_q(q))
        if unidad:
            qs = qs.filter(unidad_organica__nombre__icontains=unidad)
        if situacion:
            qs = qs.filter(situacion=situacion)
        return qs


def models_q(termino):
    from django.db.models import Q

    return Q(codigo_patrimonial__icontains=termino) | Q(denominacion__icontains=termino) | Q(serie__icontains=termino)


class DetalleBienView(LoginRequiredMixin, DetailView):
    model = Bien
    template_name = "bienes/detalle.html"
    context_object_name = "bien"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form_documento"] = DocumentoRespaldoForm()
        ctx["documentos"] = self.object.documentos.all()
        ctx["historial"] = self.object.historial_cambios.all()[:20]
        ctx["asignaciones"] = self.object.asignaciones.select_related("responsable").all()
        ctx["desplazamientos"] = self.object.desplazamientos.all()[:20]
        ctx["conservacion"] = self.object.registros_conservacion.all()[:20]
        return ctx


class CrearBienView(RolRequeridoMixin, CreateView):
    """RF06-RF07: alta del bien y generación automática del código patrimonial.

    HU-03 exige que no se pueda guardar un alta sin al menos un documento de
    respaldo: el formulario de alta (BienForm) incluye en la misma pantalla
    un segundo formulario (DocumentoRespaldoForm) y ambos se validan y
    guardan juntos, dentro de una transacción; si el documento no es válido
    (o no se adjunta ninguno), tampoco se crea el bien.
    """

    model = Bien
    form_class = BienForm
    template_name = "bienes/form.html"
    roles_permitidos = ROLES_GESTION_BIENES

    # Prefijo para evitar colisión de nombres: BienForm y DocumentoRespaldoForm
    # comparten un campo "descripcion" y ambos se renderizan en el mismo
    # <form> de bienes/form.html; sin prefijo, los dos <input name="descripcion">
    # resultantes harían que el navegador enviara una sola clave POST
    # "descripcion" y ambos formularios leyeran el mismo valor.
    PREFIJO_DOCUMENTO = "doc"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if "form_documento" not in ctx:
            if self.request.method == "POST":
                ctx["form_documento"] = DocumentoRespaldoForm(
                    self.request.POST, self.request.FILES, prefix=self.PREFIJO_DOCUMENTO
                )
            else:
                ctx["form_documento"] = DocumentoRespaldoForm(prefix=self.PREFIJO_DOCUMENTO)
        return ctx

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        form_documento = DocumentoRespaldoForm(request.POST, request.FILES, prefix=self.PREFIJO_DOCUMENTO)
        if form.is_valid() and form_documento.is_valid():
            return self.form_valid(form, form_documento)
        return self.form_invalid(form, form_documento)

    def form_valid(self, form, form_documento):
        with transaction.atomic():
            form.instance.creado_por = self.request.user
            self.object = form.save()
            form_documento.instance.bien = self.object
            form_documento.instance.cargado_por = self.request.user
            form_documento.save()
        registrar_auditoria(
            self.request.user, "ALTA_BIEN", "Bien", self.object.pk,
            f"Alta de {self.object.codigo_patrimonial} - {self.object.denominacion}",
        )
        messages.success(
            self.request,
            f"Bien registrado con el código patrimonial {self.object.codigo_patrimonial}, "
            "con su documento de respaldo adjuntado correctamente.",
        )
        return redirect(self.get_success_url())

    def form_invalid(self, form, form_documento):
        return self.render_to_response(self.get_context_data(form=form, form_documento=form_documento))

    def get_success_url(self):
        return reverse("bienes:detalle", args=[self.object.pk])


class EditarBienView(RolRequeridoMixin, UpdateView):
    """RF09: edición conservando historial de cambios."""

    model = Bien
    form_class = BienForm
    template_name = "bienes/form.html"
    roles_permitidos = ROLES_GESTION_BIENES

    def form_valid(self, form):
        anterior = Bien.objects.get(pk=self.object.pk)
        respuesta = super().form_valid(form)
        for campo in form.changed_data:
            HistorialCambioBien.objects.create(
                bien=self.object,
                campo_modificado=campo,
                valor_anterior=str(getattr(anterior, campo, "")),
                valor_nuevo=str(getattr(self.object, campo, "")),
                usuario=self.request.user,
            )
        if form.changed_data:
            registrar_auditoria(
                self.request.user, "EDICION_BIEN", "Bien", self.object.pk,
                f"Campos modificados: {', '.join(form.changed_data)}",
            )
        messages.success(self.request, "Bien actualizado correctamente.")
        return respuesta

    def get_success_url(self):
        return reverse("bienes:detalle", args=[self.object.pk])


class SubirDocumentoView(RolRequeridoMixin, CreateView):
    """RF08: adjuntar ficha técnica / documentos de respaldo."""

    model = DocumentoRespaldo
    form_class = DocumentoRespaldoForm
    template_name = "bienes/form.html"
    roles_permitidos = ROLES_GESTION_BIENES

    def dispatch(self, request, *args, **kwargs):
        self.bien = get_object_or_404(Bien, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.bien = self.bien
        form.instance.cargado_por = self.request.user
        messages.success(self.request, "Documento adjuntado correctamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("bienes:detalle", args=[self.bien.pk])
