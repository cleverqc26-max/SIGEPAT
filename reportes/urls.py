from django.urls import path

from . import views

app_name = "reportes"

urlpatterns = [
    path("", views.PanelReportesView.as_view(), name="panel"),
    path("bienes/excel/", views.ExportarBienesExcelView.as_view(), name="bienes_excel"),
    path("bienes/pdf/", views.ExportarBienesPdfView.as_view(), name="bienes_pdf"),
    path("inventario/<int:pk>/pdf/", views.ExportarInventarioPdfView.as_view(), name="inventario_pdf"),
]
