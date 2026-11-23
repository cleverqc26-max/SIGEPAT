from django import forms

from .models import RegistroConservacion


class RegistroConservacionForm(forms.ModelForm):
    class Meta:
        model = RegistroConservacion
        fields = ["estado", "observaciones", "evidencia_foto"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs.setdefault("class", "form-control")
        self.fields["estado"].widget.attrs["class"] = "form-select"
