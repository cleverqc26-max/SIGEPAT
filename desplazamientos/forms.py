from django import forms

from .models import Desplazamiento


class DesplazamientoForm(forms.ModelForm):
    class Meta:
        model = Desplazamiento
        fields = ["tipo", "origen", "destino", "motivo"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs.setdefault("class", "form-control")
        self.fields["tipo"].widget.attrs["class"] = "form-select"


class ResolucionDesplazamientoForm(forms.Form):
    decision = forms.ChoiceField(choices=[("APROBAR", "Aprobar"), ("RECHAZAR", "Rechazar")], widget=forms.RadioSelect)
    observaciones = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
