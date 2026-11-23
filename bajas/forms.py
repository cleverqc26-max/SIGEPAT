from django import forms

from .models import Baja, Saneamiento


class BajaForm(forms.ModelForm):
    class Meta:
        model = Baja
        fields = ["causal", "fecha_baja", "disposicion_final", "documentacion_sustento", "observaciones"]
        widgets = {"fecha_baja": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs.setdefault("class", "form-control")
        self.fields["causal"].widget.attrs["class"] = "form-select"
        self.fields["disposicion_final"].widget.attrs["class"] = "form-select"


class ActualizarDisposicionForm(forms.ModelForm):
    """RF26: permite actualizar la disposición final de una baja ya
    registrada (p. ej., de PENDIENTE a REMATE tras una subasta posterior)."""

    class Meta:
        model = Baja
        fields = ["disposicion_final", "documentacion_sustento", "observaciones"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs.setdefault("class", "form-control")
        self.fields["disposicion_final"].widget.attrs["class"] = "form-select"


class SaneamientoForm(forms.ModelForm):
    class Meta:
        model = Saneamiento
        fields = ["estado_tramite", "fecha_resolucion", "observaciones"]
        widgets = {"fecha_resolucion": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs.setdefault("class", "form-control")
        self.fields["estado_tramite"].widget.attrs["class"] = "form-select"
