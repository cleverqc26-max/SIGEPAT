import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, OuterRef, Subquery
from django.views.generic import TemplateView

from bienes.models import Bien
from conservacion.models import RegistroConservacion
from desplazamientos.models import Desplazamiento
from inventario.models import Inventario


class PanelDashboardView(LoginRequiredMixin, TemplateView):
    """RF31: panel con indicadores generales del patrimonio."""

    template_name = "dashboard/panel.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        total_activos = Bien.objects.filter(situacion="ACTIVO").count()
        total_baja = Bien.objects.filter(situacion="BAJA").count()

        # Distribución por estado de conservación más reciente de cada bien.
        # RNF01/RNF03: se resuelve con una única consulta (subconsulta correlacionada
        # + agregación), evitando N+1 al recorrer los bienes en Python.
        estados_choices = dict(RegistroConservacion.ESTADOS)
        conteo_estados = {codigo: 0 for codigo in estados_choices}
        sin_registrar = 0

        ultimo_estado_sq = (
            RegistroConservacion.objects.filter(bien=OuterRef("pk")).order_by("-fecha_registro").values("estado")[:1]
        )
        agregado = (
            Bien.objects.filter(situacion="ACTIVO")
            .annotate(ultimo_estado=Subquery(ultimo_estado_sq))
            .values("ultimo_estado")
            .annotate(total=Count("id"))
        )
        for fila in agregado:
            if fila["ultimo_estado"] in conteo_estados:
                conteo_estados[fila["ultimo_estado"]] = fila["total"]
            else:
                sin_registrar += fila["total"]

        # Distribución por unidad orgánica (top 10)
        por_unidad = (
            Bien.objects.filter(situacion="ACTIVO")
            .values("unidad_organica__nombre")
            .annotate(total=Count("id"))
            .order_by("-total")[:10]
        )

        inventarios_abiertos = Inventario.objects.filter(estado="EN_PROCESO")
        pendientes_verificacion = sum(inv.total_esperado - inv.total_verificado for inv in inventarios_abiertos)

        desplazamientos_pendientes = Desplazamiento.objects.filter(estado="PENDIENTE").count()

        ctx.update(
            {
                "total_bienes": total_activos + total_baja,
                "total_activos": total_activos,
                "total_baja": total_baja,
                "pendientes_verificacion": pendientes_verificacion,
                "desplazamientos_pendientes": desplazamientos_pendientes,
                "inventarios_abiertos": inventarios_abiertos,
                "datos_estado_labels": json.dumps(
                    [estados_choices[c] for c in estados_choices] + ["Sin registrar"]
                ),
                "datos_estado_valores": json.dumps(list(conteo_estados.values()) + [sin_registrar]),
                "datos_unidad_labels": json.dumps([u["unidad_organica__nombre"] for u in por_unidad]),
                "datos_unidad_valores": json.dumps([u["total"] for u in por_unidad]),
            }
        )
        return ctx
