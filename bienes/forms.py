from django import forms

from .models import Bien, DocumentoRespaldo


class BienForm(forms.ModelForm):
    class Meta:
        model = Bien
        fields = [
            "denominacion", "marca", "modelo", "serie", "categoria",
            "unidad_organica", "valor_adquisicion", "fecha_alta",
            "tipo_adquisicion", "descripcion",
        ]
        widgets = {
            "fecha_alta": forms.DateInput(attrs={"type": "date"}),
            "descripcion": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs.setdefault("class", "form-control")
        self.fields["categoria"].widget.attrs["class"] = "form-select"
        self.fields["unidad_organica"].widget.attrs["class"] = "form-select"
        self.fields["tipo_adquisicion"].widget.attrs["class"] = "form-select"


class DocumentoRespaldoForm(forms.ModelForm):
    """RF08: ficha técnica y documentos de respaldo (HU-05: valida formato/tamaño)."""

    EXTENSIONES_PERMITIDAS = ("pdf", "jpg", "jpeg", "png")
    TAMANIO_MAXIMO_MB = 10

    class Meta:
        model = DocumentoRespaldo
        fields = ["tipo_documento", "archivo", "descripcion"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs.setdefault("class", "form-control")

    def clean_archivo(self):
        archivo = self.cleaned_data["archivo"]
        extension = archivo.name.rsplit(".", 1)[-1].lower()
        if extension not in self.EXTENSIONES_PERMITIDAS:
            raise forms.ValidationError(
                f"Formato no permitido (.{extension}). Solo se aceptan: {', '.join(self.EXTENSIONES_PERMITIDAS)}."
            )
        if archivo.size > self.TAMANIO_MAXIMO_MB * 1024 * 1024:
            raise forms.ValidationError(f"El archivo supera el tamaño máximo permitido ({self.TAMANIO_MAXIMO_MB} MB).")
        return archivo


class BusquedaBienForm(forms.Form):
    """RF10: buscar y filtrar bienes."""

    q = forms.CharField(required=False, label="Código o denominación")
    unidad_organica = forms.CharField(required=False)
    situacion = forms.ChoiceField(required=False, choices=[("", "Todas")] + Bien.ESTADO_SITUACION)
