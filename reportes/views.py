from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import OuterRef, Subquery
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView, View

from bienes.models import Bien
from conservacion.models import RegistroConservacion
from inventario.models import Inventario

from .exportadores import exportar_bienes_excel, exportar_bienes_pdf, exportar_inventario_pdf
from .forms import FiltroReporteBienesForm


def _bienes_filtrados(request):
    qs = Bien.objects.select_related("categoria", "unidad_organica")
    unidad = request.GET.get("unidad_organica")
    situacion = request.GET.get("situacion")
    responsable = request.GET.get("responsable")
    estado_conservacion = request.GET.get("estado_conservacion")
    if unidad:
        qs = qs.filter(unidad_organica_id=unidad)
    if situacion:
        qs = qs.filter(situacion=situacion)
    if responsable:
        qs = qs.filter(asignaciones__activa=True, asignaciones__responsable_id=responsable)
    if estado_conservacion:
        ultimo_estado = RegistroConservacion.objects.filter(bien=OuterRef("pk")).order_by("-fecha_registro")
        qs = qs.annotate(estado_conservacion_actual_bd=Subquery(ultimo_estado.values("estado")[:1]))
        qs = qs.filter(estado_conservacion_actual_bd=estado_conservacion)
    return qs.distinct()


class PanelReportesView(LoginRequiredMixin, TemplateView):
    """RF28-RF30: panel de reportes con filtros y exportación PDF/Excel."""

    template_name = "reportes/panel.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = FiltroReporteBienesForm(self.request.GET or None)
        ctx["bienes"] = _bienes_filtrados(self.request)[:50]
        ctx["total_filtrado"] = _bienes_filtrados(self.request).count()
        ctx["inventarios"] = Inventario.objects.select_related("unidad_organica").order_by("-anio")
        return ctx


class ExportarBienesExcelView(LoginRequiredMixin, View):
    def get(self, request):
        return exportar_bienes_excel(_bienes_filtrados(request))


class ExportarBienesPdfView(LoginRequiredMixin, View):
    def get(self, request):
        return exportar_bienes_pdf(_bienes_filtrados(request))


class ExportarInventarioPdfView(LoginRequiredMixin, View):
    def get(self, request, pk):
        inventario = get_object_or_404(Inventario, pk=pk)
        return exportar_inventario_pdf(inventario)
