import os
import json

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image
)


def generar_pdf(datos, archivo_pdf):

    doc = SimpleDocTemplate(
        archivo_pdf,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )

    estilos = getSampleStyleSheet()

    contenido = []

    # LOGO
    logo = os.path.join(
        os.path.dirname(__file__),
        "static",
        "logo_inapel.png"
    )

    if os.path.exists(logo):
        img = Image(logo)
        img.drawHeight = 2.2*cm
        img.drawWidth = 2.2*cm
        contenido.append(img)

    contenido.append(Spacer(1,0.3*cm))

    # TITULOS
    titulo = estilos["Title"]
    titulo.alignment = TA_CENTER

    contenido.append(
        Paragraph(
            "INDUSTRIA NACIONAL PAPELERA S.A.S.",
            titulo
        )
    )

    contenido.append(
        Paragraph(
            "SISTEMA DE GESTIÓN DE PQR",
            estilos["Heading2"]
        )
    )

    contenido.append(
        Paragraph(
            "<b>INFORME OFICIAL DE GESTIÓN DE PQR</b>",
            estilos["Heading1"]
        )
    )

    contenido.append(Spacer(1,0.7*cm))

    # DATOS DEL PQR
    if datos:
        campos = [
            ("Radicado", datos.get("radicado", "")),
            ("Fecha recepción", str(datos.get("fechaRec", ""))),
            ("Hora", str(datos.get("horaRec", ""))),
            ("Cliente", datos.get("cliente", "")),
            ("NIT", datos.get("nit", "")),
            ("Tipo", datos.get("tipoSol", "")),
            ("Estado", datos.get("estado", "")),
            ("Prioridad", datos.get("prioridad", "")),
        ]

        data = [[Paragraph("<b>Campo</b>", estilos["Normal"]),
                 Paragraph("<b>Valor</b>", estilos["Normal"])]]
        for label, value in campos:
            data.append([
                Paragraph(f"<b>{label}:</b>", estilos["Normal"]),
                Paragraph(str(value), estilos["Normal"])
            ])

        ancho = A4[0] - 3*cm
        tbl = Table(data, colWidths=[ancho*0.3, ancho*0.7])
        tbl.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#173b74")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("LEFTPADDING", (0,0), (-1,-1), 6),
            ("RIGHTPADDING", (0,0), (-1,-1), 6),
            ("TOPPADDING", (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ]))
        contenido.append(tbl)

        desc = datos.get("desc", "")
        if desc:
            contenido.append(Spacer(1,0.3*cm))
            contenido.append(Paragraph("<b>Descripción:</b>", estilos["Normal"]))
            contenido.append(Paragraph(desc, estilos["Normal"]))

    doc.build(contenido)
