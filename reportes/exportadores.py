"""
RF30: exportación de reportes a Excel y PDF.
RF28: formato de reporte de inventario físico según la Directiva N.° 0006-2021-EF/54.01.
"""
import io

from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet


def exportar_bienes_excel(bienes):
    wb = Workbook()
    ws = wb.active
    ws.title = "Bienes patrimoniales"
    encabezados = ["Código", "Denominación", "Categoría", "Unidad orgánica", "Responsable", "Situación", "Estado conservación", "Valor (S/)"]
    ws.append(encabezados)
    for celda in ws[1]:
        celda.font = Font(bold=True, color="FFFFFF")
        celda.fill = PatternFill(start_color="1F4E5F", end_color="1F4E5F", fill_type="solid")

    for bien in bienes:
        ws.append([
            bien.codigo_patrimonial, bien.denominacion, str(bien.categoria), str(bien.unidad_organica),
            str(bien.responsable_actual or "Sin asignar"), bien.get_situacion_display(),
            bien.estado_conservacion_actual, float(bien.valor_adquisicion),
        ])
    for columna in ws.columns:
        longitud = max(len(str(c.value)) for c in columna if c.value is not None)
        ws.column_dimensions[columna[0].column_letter].width = min(max(longitud + 2, 12), 40)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    respuesta = HttpResponse(
        buffer.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    respuesta["Content-Disposition"] = 'attachment; filename="reporte_bienes.xlsx"'
    return respuesta


def exportar_bienes_pdf(bienes, titulo="Reporte de bienes patrimoniales"):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    estilos = getSampleStyleSheet()
    elementos = [
        Paragraph("Municipalidad Distrital de Unión Asháninka", estilos["Heading3"]),
        Paragraph(titulo, estilos["Heading2"]),
        Spacer(1, 12),
    ]
    data = [["Código", "Denominación", "Categoría", "Unidad orgánica", "Responsable", "Situación"]]
    for bien in bienes:
        data.append([
            bien.codigo_patrimonial, bien.denominacion, str(bien.categoria), str(bien.unidad_organica),
            str(bien.responsable_actual or "Sin asignar"), bien.get_situacion_display(),
        ])
    tabla = Table(data, repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E5F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EAF1F3")]),
    ]))
    elementos.append(tabla)
    doc.build(elementos)
    buffer.seek(0)
    respuesta = HttpResponse(buffer.read(), content_type="application/pdf")
    respuesta["Content-Disposition"] = 'attachment; filename="reporte_bienes.pdf"'
    return respuesta


def exportar_inventario_pdf(inventario):
    """RF28: formato de acta de inventario físico (Directiva N.° 0006-2021-EF/54.01).

    Se usa orientación horizontal (landscape) y anchos de columna fijos para
    que la tabla siempre quepa dentro de la página, sin recortarse — antes
    quedaba cortada porque el ancho de las columnas se calculaba solo, y con
    textos largos (p. ej. la descripción de un sobrante) superaba el ancho
    de una A4 vertical.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4),
        topMargin=1.3 * cm, bottomMargin=1.3 * cm, leftMargin=1.3 * cm, rightMargin=1.3 * cm,
    )
    estilos = getSampleStyleSheet()
    estilo_normal = estilos["Normal"]
    estilo_normal.fontSize = 9

    pendientes = max(inventario.total_esperado - inventario.total_verificado - inventario.total_faltantes, 0)

    elementos = [
        Paragraph("Municipalidad Distrital de Unión Asháninka", estilos["Heading3"]),
        Paragraph("Acta de Inventario Físico de Bienes Muebles Patrimoniales", estilos["Heading2"]),
        Paragraph("Elaborada conforme a la Directiva N.° 0006-2021-EF/54.01", estilo_normal),
        Spacer(1, 10),
        Paragraph(f"<b>Año:</b> {inventario.anio} &nbsp;&nbsp; <b>Unidad orgánica:</b> {inventario.unidad_organica}", estilo_normal),
        Paragraph(f"<b>Periodo:</b> {inventario.fecha_inicio} al {inventario.fecha_cierre or '(en proceso)'}", estilo_normal),
        Paragraph(f"<b>Responsable:</b> {inventario.responsable}", estilo_normal),
        Spacer(1, 10),
        Paragraph(
            f"<b>Bienes esperados:</b> {inventario.total_esperado} &nbsp;·&nbsp; "
            f"<b>Verificados conformes:</b> {inventario.total_verificado} &nbsp;·&nbsp; "
            f"<b>Sobrantes:</b> {inventario.total_sobrantes} &nbsp;·&nbsp; "
            f"<b>Faltantes:</b> {inventario.total_faltantes} &nbsp;·&nbsp; "
            f"<b>Pendientes de verificar:</b> {pendientes}",
            estilo_normal,
        ),
        Spacer(1, 12),
    ]

    estilo_celda = ParagraphStyle("celda", parent=estilos["Normal"], fontSize=7.5, leading=9)
    estilo_encabezado = ParagraphStyle("encabezado", parent=estilo_celda, textColor=colors.white, fontName="Helvetica-Bold")

    encabezados = ["Bien / hallazgo", "Resultado", "Ubicación", "Estado conservación", "Responsable encontrado", "Fecha verificación", "Verificado por"]
    data = [[Paragraph(h, estilo_encabezado) for h in encabezados]]
    for v in inventario.verificaciones.select_related("bien", "responsable_encontrado", "verificado_por").order_by("resultado"):
        fila = [
            v.bien.codigo_patrimonial if v.bien_id else v.descripcion_hallazgo,
            v.get_resultado_display(),
            v.ubicacion_encontrada,
            v.estado_conservacion_encontrado or "—",
            str(v.responsable_encontrado) if v.responsable_encontrado_id else "—",
            v.fecha_verificacion.strftime("%d/%m/%Y") if v.fecha_verificacion else "—",
            str(v.verificado_por) if v.verificado_por_id else "—",
        ]
        data.append([Paragraph(str(celda), estilo_celda) for celda in fila])

    # Anchos fijos (en cm) que suman el ancho disponible en A4 horizontal
    # (29.7cm - 2*1.3cm de márgenes = 27.1cm) para que nunca se corte.
    anchos = [c * cm for c in (5.5, 3.2, 4.2, 3.2, 4.5, 3.0, 3.5)]
    tabla = Table(data, colWidths=anchos, repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E5F")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EAF1F3")]),
    ]))
    elementos.append(tabla)
    doc.build(elementos)
    buffer.seek(0)
    respuesta = HttpResponse(buffer.read(), content_type="application/pdf")
    respuesta["Content-Disposition"] = f'attachment; filename="acta_inventario_{inventario.anio}.pdf"'
    return respuesta


def exportar_desplazamientos_excel(desplazamientos):
    """RF17: exportación propia del historial de desplazamientos (no depende
    del exportador de bienes del módulo de reportes)."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Desplazamientos"
    encabezados = [
        "Bien", "Tipo", "Origen", "Destino", "Solicitante", "Estado",
        "Autorizado por", "Fecha solicitud", "Fecha resolución",
    ]
    ws.append(encabezados)
    for celda in ws[1]:
        celda.font = Font(bold=True, color="FFFFFF")
        celda.fill = PatternFill(start_color="1F4E5F", end_color="1F4E5F", fill_type="solid")

    for d in desplazamientos:
        ws.append([
            d.bien.codigo_patrimonial, d.get_tipo_display(), d.origen, d.destino,
            str(d.solicitante), d.get_estado_display(),
            str(d.autorizado_por) if d.autorizado_por_id else "—",
            d.fecha_solicitud.strftime("%d/%m/%Y %H:%M") if d.fecha_solicitud else "",
            d.fecha_resolucion.strftime("%d/%m/%Y %H:%M") if d.fecha_resolucion else "",
        ])
    for columna in ws.columns:
        longitud = max(len(str(c.value)) for c in columna if c.value is not None)
        ws.column_dimensions[columna[0].column_letter].width = min(max(longitud + 2, 12), 40)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    respuesta = HttpResponse(
        buffer.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    respuesta["Content-Disposition"] = 'attachment; filename="reporte_desplazamientos.xlsx"'
    return respuesta
