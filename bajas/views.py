from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, TemplateView, UpdateView, View

from auditoria.models import registrar_auditoria
from bienes.models import Bien
from catalogos.models import Rol
from cuentas.mixins import RolRequeridoMixin
from inventario.models import VerificacionInventario

from .forms import ActualizarDisposicionForm, BajaForm, SaneamientoForm
from .models import Baja, Saneamiento

ROLES_BAJAS = (Rol.CONTROL_PATRIMONIAL, Rol.ADMINISTRADOR)


class PanelBajasSaneamientoView(LoginRequiredMixin, TemplateView):
    """Panel único: bajas registradas + saneamientos pendientes (RF25-RF27)."""

    template_name = "bajas/lista.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["bajas"] = Baja.objects.select_related("bien", "causal").order_by("-fecha_baja")[:50]
        ctx["saneamientos"] = Saneamiento.objects.select_related("verificacion__bien", "verificacion__inventario").order_by("-fecha_inicio_tramite")[:50]
        # RF27: sobrantes/faltantes detectados que aún no tienen saneamiento iniciado
        pendientes = VerificacionInventario.objects.filter(
            resultado__in=["SOBRANTE", "FALTANTE"], saneamiento__isnull=True
        ).select_related("bien", "inventario")
        ctx["pendientes_saneamiento"] = pendientes
        return ctx


class CrearBajaView(RolRequeridoMixin, CreateView):
    """RF25-RF26: registrar la baja de un bien con su causal y disposición final."""

    model = Baja
    form_class = BajaForm
    template_name = "bajas/form_baja.html"
    roles_permitidos = ROLES_BAJAS

    def dispatch(self, request, *args, **kwargs):
        self.bien = get_object_or_404(Bien, pk=kwargs["bien_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["bien"] = self.bien
        return ctx

    def form_valid(self, form):
        form.instance.bien = self.bien
        form.instance.registrado_por = self.request.user
        respuesta = super().form_valid(form)
        registrar_auditoria(
            self.request.user, "BAJA_BIEN", "Bien", self.bien.pk,
            f"Causal: {self.object.causal}",
        )
        messages.success(self.request, f"Baja registrada para {self.bien.codigo_patrimonial}.")
        return respuesta

    def get_success_url(self):
        return reverse("bienes:detalle", args=[self.bien.pk])


class ActualizarDisposicionBajaView(RolRequeridoMixin, UpdateView):
    """RF26: actualizar la disposición final de una baja ya registrada
    (no existía ninguna vista de edición posterior; solo se fijaba en el
    momento de registrar la baja)."""

    model = Baja
    form_class = ActualizarDisposicionForm
    template_name = "bajas/form_disposicion.html"
    roles_permitidos = ROLES_BAJAS
    success_url = reverse_lazy("bajas:lista")

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        registrar_auditoria(
            self.request.user, "BAJA_DISPOSICION_ACTUALIZADA", "Baja", self.object.pk,
            f"Disposición final actualizada a {self.object.get_disposicion_final_display()}",
        )
        messages.success(self.request, "Disposición final actualizada correctamente.")
        return respuesta


class IniciarSaneamientoView(RolRequeridoMixin, View):
    """RF27: inicia el trámite de saneamiento para un sobrante/faltante detectado en inventario."""

    roles_permitidos = ROLES_BAJAS

    def post(self, request, verificacion_pk):
        verificacion = get_object_or_404(
            VerificacionInventario, pk=verificacion_pk, resultado__in=["SOBRANTE", "FALTANTE"]
        )
        if not hasattr(verificacion, "saneamiento"):
            Saneamiento.objects.create(
                verificacion=verificacion,
                tipo=verificacion.resultado,
                fecha_inicio_tramite=timezone.now().date(),
            )
            registrar_auditoria(
                request.user, "SANEAMIENTO", "VerificacionInventario", verificacion.pk,
                f"Inicio de saneamiento tipo {verificacion.resultado}",
            )
            messages.success(request, "Trámite de saneamiento iniciado.")
        return redirect("bajas:lista")


class ActualizarSaneamientoView(RolRequeridoMixin, UpdateView):
    """RF27: actualizar el estado del trámite de saneamiento."""

    model = Saneamiento
    form_class = SaneamientoForm
    template_name = "bajas/form_saneamiento.html"
    roles_permitidos = ROLES_BAJAS
    success_url = reverse_lazy("bajas:lista")

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        registrar_auditoria(
            self.request.user, "SANEAMIENTO", "Saneamiento", self.object.pk,
            f"Estado: {self.object.estado_tramite}",
        )
        messages.success(self.request, "Saneamiento actualizado.")
        return respuesta
