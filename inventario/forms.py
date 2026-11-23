from django import forms

from bienes.models import Bien

from .models import Inventario, VerificacionInventario


class InventarioForm(forms.ModelForm):
    class Meta:
        model = Inventario
        fields = ["anio", "unidad_organica", "fecha_inicio"]
        widgets = {"fecha_inicio": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs.setdefault("class", "form-control")
        self.fields["unidad_organica"].widget.attrs["class"] = "form-select"


class VerificacionForm(forms.ModelForm):
    """RF21: verificación física; si el bien no está en el registro, se
    completa 'descripcion_hallazgo' y el resultado queda como SOBRANTE."""

    class Meta:
        model = VerificacionInventario
        # "origen_dispositivo" NO se expone al usuario: es referencial
        # (WEB/MOVIL, RNF07) y la vista lo determina automáticamente a
        # partir del dispositivo desde el que se envía el formulario.
        fields = [
            "bien", "descripcion_hallazgo", "resultado",
            "ubicacion_encontrada", "estado_conservacion_encontrado",
        ]

    def __init__(self, *args, unidad_organica=None, **kwargs):
        super().__init__(*args, **kwargs)
        if unidad_organica is not None:
            self.fields["bien"].queryset = Bien.objects.filter(
                unidad_organica=unidad_organica, situacion="ACTIVO"
            )
        self.fields["bien"].required = False
        for campo in self.fields.values():
            campo.widget.attrs.setdefault("class", "form-control")
        self.fields["bien"].widget.attrs["class"] = "form-select"
        self.fields["resultado"].widget.attrs["class"] = "form-select"

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("resultado") == "SOBRANTE" and not cleaned.get("descripcion_hallazgo"):
            self.add_error("descripcion_hallazgo", "Describe el bien hallado que no está registrado.")
        if cleaned.get("resultado") != "SOBRANTE" and not cleaned.get("bien"):
            self.add_error("bien", "Selecciona el bien verificado.")
        return cleaned


class CierreInventarioForm(forms.Form):
    observaciones_cierre = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}))


class ConciliacionForm(forms.Form):
    """RF24: conciliación entre el resultado del inventario y los registros de contabilidad."""

    observaciones_conciliacion = forms.CharField(
        label="Observaciones de la conciliación",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )
