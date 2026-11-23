from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import CreateView, ListView

from auditoria.models import registrar_auditoria
from bienes.models import Bien
from catalogos.models import Rol
from cuentas.mixins import RolRequeridoMixin

from .forms import AsignacionForm
from .models import Asignacion


class ListaAsignacionesView(LoginRequiredMixin, ListView):
    model = Asignacion
    template_name = "asignaciones/lista.html"
    context_object_name = "asignaciones"
    paginate_by = 20

    def get_queryset(self):
        qs = Asignacion.objects.select_related("bien", "responsable").order_by("-fecha_asignacion")
        if not (self.request.user.es_administrador or self.request.user.es_control_patrimonial):
            qs = qs.filter(responsable=self.request.user)
        return qs


class CrearAsignacionView(RolRequeridoMixin, CreateView):
    """RF11-RF12: asignar (o reasignar) un bien a un responsable."""

    model = Asignacion
    form_class = AsignacionForm
    template_name = "asignaciones/form.html"
    roles_permitidos = (Rol.CONTROL_PATRIMONIAL, Rol.ADMINISTRADOR)

    def dispatch(self, request, *args, **kwargs):
        self.bien = get_object_or_404(Bien, pk=kwargs["bien_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["bien"] = self.bien
        return ctx

    def form_valid(self, form):
        # RF12: cierra la asignación activa anterior (si existe) antes de crear la nueva.
        asignacion_previa = self.bien.asignaciones.filter(activa=True).first()
        accion = "REASIGNACION" if asignacion_previa else "ASIGNACION"
        if asignacion_previa:
            asignacion_previa.cerrar(form.cleaned_data["fecha_asignacion"])

        form.instance.bien = self.bien
        form.instance.asignado_por = self.request.user
        respuesta = super().form_valid(form)

        registrar_auditoria(
            self.request.user, accion, "Asignacion", self.object.pk,
            f"{self.bien.codigo_patrimonial} -> {self.object.responsable}",
        )
        messages.success(self.request, f"Bien asignado a {self.object.responsable} (acta {self.object.numero_acta}).")
        return respuesta

    def get_success_url(self):
        return reverse("bienes:detalle", args=[self.bien.pk])
