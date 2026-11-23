from django import forms

from bienes.models import Bien
from catalogos.models import Rol, UnidadOrganica
from conservacion.models import RegistroConservacion
from cuentas.models import Usuario


class FiltroReporteBienesForm(forms.Form):
    """RF29: reportes de bienes filtrados por unidad orgánica, responsable, estado o situación."""

    unidad_organica = forms.ModelChoiceField(
        queryset=UnidadOrganica.objects.all(), required=False, label="Unidad orgánica"
    )
    situacion = forms.ChoiceField(choices=[("", "Todas")] + Bien.ESTADO_SITUACION, required=False)
    responsable = forms.ModelChoiceField(
        queryset=Usuario.objects.filter(rol__codigo=Rol.RESPONSABLE, is_active=True).order_by("first_name", "last_name"),
        required=False, label="Responsable",
    )
    estado_conservacion = forms.ChoiceField(
        choices=[("", "Todos")] + RegistroConservacion.ESTADOS, required=False, label="Estado de conservación",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs.setdefault("class", "form-select")
