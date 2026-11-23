from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView, ListView, View

from auditoria.models import registrar_auditoria
from bienes.models import Bien
from catalogos.models import Rol
from cuentas.mixins import RolRequeridoMixin

from reportes.exportadores import exportar_desplazamientos_excel

from .forms import DesplazamientoForm, ResolucionDesplazamientoForm
from .models import Desplazamiento


class ListaDesplazamientosView(LoginRequiredMixin, ListView):
    model = Desplazamiento
    template_name = "desplazamientos/lista.html"
    context_object_name = "desplazamientos"
    paginate_by = 20

    def get_queryset(self):
        return Desplazamiento.objects.select_related("bien", "solicitante").order_by("-fecha_solicitud")


class CrearDesplazamientoView(LoginRequiredMixin, CreateView):
    """RF14: registrar solicitud de desplazamiento interno/externo."""

    model = Desplazamiento
    form_class = DesplazamientoForm
    template_name = "desplazamientos/form.html"

    def dispatch(self, request, *args, **kwargs):
        self.bien = get_object_or_404(Bien, pk=kwargs["bien_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["bien"] = self.bien
        return ctx

    def form_valid(self, form):
        form.instance.bien = self.bien
        form.instance.solicitante = self.request.user
        respuesta = super().form_valid(form)
        registrar_auditoria(
            self.request.user, "DESPLAZAMIENTO_SOLICITADO", "Desplazamiento", self.object.pk,
            f"{self.bien.codigo_patrimonial}: {self.object.origen} -> {self.object.destino}",
        )
        messages.success(self.request, "Solicitud de desplazamiento registrada. Queda pendiente de autorización (RF15).")
        return respuesta

    def get_success_url(self):
        return reverse("bienes:detalle", args=[self.bien.pk])


class ResolverDesplazamientoView(RolRequeridoMixin, View):
    """RF15-RF16: autorizar o rechazar un desplazamiento; al aprobar se
    actualiza la ubicación (unidad orgánica) del bien."""

    roles_permitidos = (Rol.CONTROL_PATRIMONIAL, Rol.ADMINISTRADOR)

    def post(self, request, pk):
        desplazamiento = get_object_or_404(Desplazamiento, pk=pk, estado="PENDIENTE")
        form = ResolucionDesplazamientoForm(request.POST)
        if form.is_valid():
            ahora = timezone.now()
            if form.cleaned_data["decision"] == "APROBAR":
                desplazamiento.aprobar(request.user, ahora)
                bien = desplazamiento.bien
                # RF16: actualizar automáticamente la ubicación del bien.
                from catalogos.models import UnidadOrganica

                destino, _ = UnidadOrganica.objects.get_or_create(nombre=desplazamiento.destino)
                bien.unidad_organica = destino
                bien.save(update_fields=["unidad_organica"])
                registrar_auditoria(
                    request.user, "DESPLAZAMIENTO_APROBADO", "Desplazamiento", desplazamiento.pk,
                    f"Aprobado hacia {desplazamiento.destino}",
                )
                messages.success(request, "Desplazamiento aprobado. Ubicación del bien actualizada.")
            else:
                desplazamiento.rechazar(request.user, ahora, form.cleaned_data["observaciones"])
                registrar_auditoria(
                    request.user, "DESPLAZAMIENTO_RECHAZADO", "Desplazamiento", desplazamiento.pk, ""
                )
                messages.info(request, "Desplazamiento rechazado.")
        return redirect("desplazamientos:lista")


class ExportarDesplazamientosExcelView(LoginRequiredMixin, View):
    """RF17: exportación propia del historial de desplazamientos a Excel."""

    def get(self, request):
        desplazamientos = Desplazamiento.objects.select_related(
            "bien", "solicitante", "autorizado_por"
        ).order_by("-fecha_solicitud")
        return exportar_desplazamientos_excel(desplazamientos)
