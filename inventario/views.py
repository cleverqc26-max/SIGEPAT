from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView, View

from auditoria.models import registrar_auditoria
from catalogos.models import Rol
from cuentas.mixins import RolRequeridoMixin

from .forms import CierreInventarioForm, ConciliacionForm, InventarioForm, VerificacionForm
from .models import Inventario, VerificacionInventario

ROLES_INVENTARIO = (Rol.CONTROL_PATRIMONIAL, Rol.ADMINISTRADOR)
ROLES_CONCILIACION = (Rol.CONTABILIDAD, Rol.ADMINISTRADOR)


class ListaInventariosView(LoginRequiredMixin, ListView):
    model = Inventario
    template_name = "inventario/lista.html"
    context_object_name = "inventarios"
    paginate_by = 20

    def get_queryset(self):
        return Inventario.objects.select_related("unidad_organica", "responsable").order_by("-anio")


class CrearInventarioView(RolRequeridoMixin, CreateView):
    """RF20: programar y ejecutar un inventario físico por periodo."""

    model = Inventario
    form_class = InventarioForm
    template_name = "inventario/form.html"
    roles_permitidos = ROLES_INVENTARIO

    def form_valid(self, form):
        form.instance.responsable = self.request.user
        respuesta = super().form_valid(form)
        registrar_auditoria(
            self.request.user, "INVENTARIO_ABIERTO", "Inventario", self.object.pk,
            f"{self.object.anio} - {self.object.unidad_organica}",
        )
        messages.success(self.request, "Inventario físico abierto correctamente.")
        return respuesta

    def get_success_url(self):
        return reverse("inventario:detalle", args=[self.object.pk])


class DetalleInventarioView(LoginRequiredMixin, DetailView):
    model = Inventario
    template_name = "inventario/detalle.html"
    context_object_name = "inventario"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form_verificacion"] = VerificacionForm(unidad_organica=self.object.unidad_organica)
        ctx["form_cierre"] = CierreInventarioForm()
        ctx["form_conciliacion"] = ConciliacionForm()
        ctx["verificaciones"] = self.object.verificaciones.select_related("bien", "verificado_por").order_by("-fecha_verificacion")
        bienes_verificados_ids = self.object.verificaciones.exclude(bien=None).values_list("bien_id", flat=True)
        ctx["bienes_pendientes"] = self.object.bienes_esperados.exclude(id__in=bienes_verificados_ids)
        return ctx


class RegistrarVerificacionView(RolRequeridoMixin, View):
    """RF21: registrar la verificación física de cada bien (incluye acceso móvil, RNF07)."""

    roles_permitidos = ROLES_INVENTARIO

    def post(self, request, pk):
        inventario = get_object_or_404(Inventario, pk=pk, estado="EN_PROCESO")
        form = VerificacionForm(request.POST, unidad_organica=inventario.unidad_organica)
        if form.is_valid():
            verificacion = form.save(commit=False)
            verificacion.inventario = inventario
            verificacion.verificado_por = request.user
            # RNF07: referencial, inferido del User-Agent (no lo llena el usuario).
            ua = request.META.get("HTTP_USER_AGENT", "").lower()
            verificacion.origen_dispositivo = "MOVIL" if any(
                token in ua for token in ("mobile", "android", "iphone")
            ) else "WEB"
            verificacion.save()
            messages.success(request, "Verificación registrada.")
        else:
            messages.error(request, f"No se pudo registrar la verificación: {form.errors.as_text()}")
        return redirect("inventario:detalle", pk=pk)


class CerrarInventarioView(RolRequeridoMixin, View):
    """RF22-RF23: al cerrar, genera automáticamente los bienes FALTANTES
    (esperados y no verificados) y produce el acta de cierre."""

    roles_permitidos = ROLES_INVENTARIO

    def post(self, request, pk):
        inventario = get_object_or_404(Inventario, pk=pk, estado="EN_PROCESO")
        form = CierreInventarioForm(request.POST)
        if form.is_valid():
            verificados_ids = inventario.verificaciones.exclude(bien=None).values_list("bien_id", flat=True)
            faltantes = inventario.bienes_esperados.exclude(id__in=verificados_ids)
            for bien in faltantes:
                VerificacionInventario.objects.create(
                    inventario=inventario, bien=bien, resultado="FALTANTE",
                    verificado_por=request.user,
                )
            from django.utils import timezone

            inventario.cerrar(timezone.now().date(), form.cleaned_data["observaciones_cierre"])
            registrar_auditoria(
                request.user, "INVENTARIO_CERRADO", "Inventario", inventario.pk,
                f"Sobrantes={inventario.total_sobrantes} Faltantes={inventario.total_faltantes}",
            )
            messages.success(
                request,
                f"Inventario cerrado. Sobrantes: {inventario.total_sobrantes} · "
                f"Faltantes: {inventario.total_faltantes}.",
            )
        return redirect("inventario:detalle", pk=pk)


class ConciliarInventarioView(RolRequeridoMixin, View):
    """RF24: registrar la conciliación entre el resultado del inventario físico
    ya cerrado y los registros de contabilidad. Flujo de negocio dedicado para
    el rol Contabilidad (antes solo era editable desde /admin/ de Django)."""

    roles_permitidos = ROLES_CONCILIACION

    def post(self, request, pk):
        inventario = get_object_or_404(Inventario, pk=pk, estado="CERRADO")
        form = ConciliacionForm(request.POST)
        if form.is_valid():
            inventario.conciliar(request.user, form.cleaned_data["observaciones_conciliacion"])
            registrar_auditoria(
                request.user, "INVENTARIO_CONCILIADO", "Inventario", inventario.pk,
                f"Conciliación contable registrada por {request.user}",
            )
            messages.success(request, "Conciliación con contabilidad registrada correctamente.")
        return redirect("inventario:detalle", pk=pk)
