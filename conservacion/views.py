from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import CreateView

from bienes.models import Bien
from catalogos.models import Rol
from cuentas.mixins import RolRequeridoMixin

from .forms import RegistroConservacionForm
from .models import RegistroConservacion


class CrearRegistroConservacionView(RolRequeridoMixin, CreateView):
    """RF18-RF19: registrar estado de conservación con evidencia fotográfica."""

    model = RegistroConservacion
    form_class = RegistroConservacionForm
    template_name = "conservacion/form.html"
    roles_permitidos = (Rol.CONTROL_PATRIMONIAL, Rol.ADMINISTRADOR)

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
        messages.success(self.request, "Estado de conservación registrado.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("bienes:detalle", args=[self.bien.pk])
