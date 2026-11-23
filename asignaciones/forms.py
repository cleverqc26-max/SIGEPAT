from django import forms

from cuentas.models import Usuario

from .models import Asignacion


class AsignacionForm(forms.ModelForm):
    class Meta:
        model = Asignacion
        fields = ["responsable", "fecha_asignacion", "observaciones"]
        widgets = {"fecha_asignacion": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["responsable"].queryset = Usuario.objects.filter(is_active=True).order_by("first_name")
        for campo in self.fields.values():
            campo.widget.attrs.setdefault("class", "form-control")
        self.fields["responsable"].widget.attrs["class"] = "form-select"
