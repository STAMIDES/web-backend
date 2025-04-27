import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime
import models as m # Assuming models.py contains the Enum definitions

def format_time(time_obj):
    """Formats a datetime.time object into HH:MM string."""
    if time_obj:
        return time_obj.strftime('%H:%M')
    return 'N/A'

def generate_planificacion_pdf(planificacion_data):
    """Generates a PDF document for a given planification."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                        leftMargin=0.5*inch, rightMargin=0.5*inch,
                        topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    story = []

    # Title - Handle both dict and object access
    is_dict = isinstance(planificacion_data, dict)
    plan_id = planificacion_data.get('id', 'N/A') if is_dict else getattr(planificacion_data, 'id', 'N/A')
    plan_fecha_obj = planificacion_data.get('fecha') if is_dict else getattr(planificacion_data, 'fecha', None)
    plan_fecha = plan_fecha_obj.strftime('%d/%m/%Y') if plan_fecha_obj else 'N/A'
    title = f"Planificación ID: {plan_id} - Fecha: {plan_fecha}"
    story.append(Paragraph(title, styles['h1']))
    story.append(Spacer(1, 0.2*inch))

    # Routes - Handle both dict and object access
    rutas = planificacion_data.get('rutas', []) if is_dict else getattr(planificacion_data, 'rutas', [])
    if not rutas:
        story.append(Paragraph("No hay rutas asignadas para esta planificación.", styles['Normal']))
    
    for i, ruta in enumerate(rutas):
        story.append(Paragraph(f"Ruta {i+1}", styles['h2']))
        
        # Route Header Info
        vehiculo = ruta.vehiculo
        chofer_info = ruta.chofer if ruta.chofer else None # Assuming one chofer per route for simplicity
        
        header_data = [
            [Paragraph("<b>Vehículo:</b>", styles['Normal']), Paragraph(f"{vehiculo.matricula} ({vehiculo.descripcion})" if vehiculo else 'N/A', styles['Normal'])],
            [Paragraph("<b>Chofer:</b>", styles['Normal']), Paragraph(f"{chofer_info.nombre} {chofer_info.apellido}" if chofer_info else 'N/A', styles['Normal'])],
            [Paragraph("<b>Hora Inicio:</b>", styles['Normal']), Paragraph(format_time(ruta.hora_inicio), styles['Normal'])],
            [Paragraph("<b>Hora Fin:</b>", styles['Normal']), Paragraph(format_time(ruta.hora_fin), styles['Normal'])],
        ]
        header_table = Table(header_data, colWidths=[1.5*inch, 5.5*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 0.15*inch))

        # Visits Table
        visitas_data = [[Paragraph("<b>Hora Llegada</b>", styles['Normal']), Paragraph("<b>Dirección / Lugar</b>", styles['Normal'])]]
        
        # Access visits using getattr to be safe
        visitas = sorted(getattr(ruta, 'visitas', []), key=lambda v: getattr(v, 'hora_llegada', None) or datetime.min.time()) # Ensure visits are sorted by time
        
        for visita in visitas:
            hora_llegada = format_time(getattr(visita, 'hora_llegada', None))
            direccion = ""
            tipo_item = getattr(visita, 'tipo_item', None)
            item = getattr(visita, 'item', None)
            
            if tipo_item == m.TipoItemVisita.parada:
                direccion = getattr(item, 'direccion', 'Parada no encontrada') if item else 'Parada no encontrada'
            elif tipo_item == m.TipoItemVisita.lugar_comun:
                direccion = getattr(item, 'nombre', 'Lugar común no encontrado') if item else 'Lugar común no encontrado'
            else:
                 direccion = "Tipo de item desconocido"

            visitas_data.append([Paragraph(hora_llegada, styles['Normal']), Paragraph(direccion, styles['Normal'])])

        if len(visitas_data) > 1:
            visitas_table = Table(visitas_data, colWidths=[1.5*inch, 5.5*inch])
            visitas_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.grey),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('BACKGROUND', (0,1), (-1,-1), colors.beige),
                ('GRID', (0,0), (-1,-1), 1, colors.black),
                ('ALIGN', (1,1), (1,-1), 'LEFT'), # Align address column to the left
                ('LEFTPADDING', (1,1), (1,-1), 6),
            ]))
            story.append(visitas_table)
        else:
            story.append(Paragraph("No hay visitas asignadas para esta ruta.", styles['Normal']))

        story.append(Spacer(1, 0.3*inch))

    doc.build(story)
    buffer.seek(0)
    return buffer
