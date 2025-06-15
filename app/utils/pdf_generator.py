import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime, timedelta, time
import models as model
from database import get_pedido_and_cliente_db
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from collections import defaultdict, Counter
import numpy as np
from io import BytesIO
import base64
import logging

log = logging.getLogger(__name__)

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
    # Create a smaller font style for the table content
    small_style = ParagraphStyle('Small', parent=styles['Normal'], fontSize=8)
    story = []

    # Cache for pedidos to avoid redundant database calls
    pedidos_cache = {}

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
        visitas_data = [[Paragraph("<b>Hora</b>", small_style), 
                         Paragraph("<b>HMax.</b>", small_style), 
                         Paragraph("<b>Acción</b>", small_style),
                         Paragraph("<b>Dirección / Lugar</b>", small_style),
                         Paragraph("<b>Contacto Usuario</b>", small_style)]]
        
        # Access visits using getattr to be safe
        visitas = sorted(getattr(ruta, 'visitas', []), key=lambda v: getattr(v, 'hora_calculada_de_llegada', None) or datetime.min.time()) # Ensure visits are sorted by time
        
        # Dictionary to track client document appearances
        cliente_documento_count = defaultdict(int)
        
        for visita in visitas:
            hora_calculada_de_llegada = format_time(getattr(visita, 'hora_calculada_de_llegada', None))
            hora_pedida = format_time(getattr(visita, 'hora_pedida', None))

            direccion = ""
            accion = ""
            contacto = "N/A"  # Default contact info
            tipo_item = getattr(visita, 'tipo_item', None)
            if tipo_item == model.TipoItemVisita.parada:
                item = getattr(visita, 'parada', None)
                direccion = getattr(item, 'direccion', 'Parada no encontrada') if item else 'Parada no encontrada'
                
                id_pedido = getattr(item, 'id_pedido', None)
                pedido = None
                cliente = None
                if id_pedido:
                    # Check cache first
                    if id_pedido in pedidos_cache:
                        pedido = pedidos_cache[id_pedido]
                    else:
                        # Get from database and cache it
                        pedido = get_pedido_and_cliente_db(id_pedido)
                        pedidos_cache[id_pedido] = pedido
                    
                    if pedido:
                        cliente = getattr(pedido, 'cliente', None)
                
                if cliente:
                    nombre = getattr(cliente, 'nombre', '')
                    apellido = getattr(cliente, 'apellido', '')
                    documento = getattr(cliente, 'documento', '')
                    
                    # Get client contact information
                    telefono = getattr(cliente, 'telefono', None)
                    email = getattr(cliente, 'email', None)
                    
                    if telefono:
                        contacto = f"tel: {telefono}"
                    elif email:
                        contacto = f"mail: {email}"
                    
                    # Count appearances for this client
                    cliente_documento_count[documento] += 1
                    
                    # Determine if pick up or drop off
                    if cliente_documento_count[documento] % 2 == 1:  # Odd count = pickup
                        accion = f"Recoger a {nombre} {apellido}"
                    else:  # Even count = dropoff
                        accion = f"Dejar a {nombre} {apellido}"
                    
                    # Check for special conditions
                    caracteristicas = getattr(cliente, 'caracteristicas', [])
                    special_conditions = []
                    
                    for caracteristica in caracteristicas:
                        nombre_caracteristica = getattr(caracteristica, 'nombre', '')
                        if nombre_caracteristica == 'silla_de_ruedas':
                            special_conditions.append('Usa silla de ruedas')
                        elif nombre_caracteristica == 'rampa_electrica':
                            special_conditions.append('Precisa rampa eléctrica')
                        elif nombre_caracteristica:  # Include any other characteristic
                            special_conditions.append(nombre_caracteristica)
                    
                    # Add acompañante info
                    if pedido and getattr(pedido, 'acompañante', False):
                        special_conditions.append('Con acompañante')
                    
                    # Add special conditions to action text
                    if special_conditions:
                        accion += f" ({', '.join(special_conditions)})"
                else:
                    accion = "No especificado"
            
            elif tipo_item == model.TipoItemVisita.lugar_comun:
                item = getattr(visita, 'lugar_comun', None)
                direccion = getattr(item, 'nombre', 'Lugar común no encontrado') if item else 'Lugar común no encontrado'
                direccion += f"<br/> ({getattr(item, 'direccion', 'Sin dirección')})" if item else ''
                # Determine if it's start or end based on position in route
                if visitas.index(visita) == 0:
                    accion = "Comienzo"
                elif visitas.index(visita) == len(visitas) - 1:
                    accion = "Fin"
                else:
                    accion = "Parada intermedia"
            else:
                direccion = "Tipo de item desconocido"  
                accion = "Acción desconocida"

            visitas_data.append([Paragraph(hora_calculada_de_llegada, small_style),
                                 Paragraph(hora_pedida, small_style),
                                Paragraph(accion, small_style),
                                Paragraph(direccion, small_style),
                                Paragraph(contacto, small_style)])

        # Add driver's rest period if available
        descanso_inicio = getattr(ruta, 'descanso_inicio', None)
        descanso_fin = getattr(ruta, 'descanso_fin', None)
        
        if descanso_inicio and descanso_fin:
            # Format rest times
            descanso_inicio_str = format_time(descanso_inicio)
            descanso_fin_str = format_time(descanso_fin)
            
            # Create rest period row with coffee emoji
            rest_row = [
                Paragraph(descanso_inicio_str, small_style),
                Paragraph("---", small_style),  # Empty cell for hora_pedida
                Paragraph("Descanso del conductor", small_style),
                Paragraph(f"Duración: {descanso_inicio_str} - {descanso_fin_str}", small_style),
                Paragraph("---", small_style)
            ]
            
            # Find the correct position to insert the rest period based on time
            inserted = False
            for i in range(1, len(visitas_data)):
                visita_hora_str = visitas_data[i][0].text
                log.info(f"Comparing rest start {descanso_inicio_str} with visit time {visita_hora_str}")
                # Convert string times to datetime.time objects for comparison
                try:
                    # Extract hours and minutes from the time string (assumed format 'HH:MM')
                    h, m = map(int, visita_hora_str.split(':'))
                    visita_hora = time(hour=h, minute=m)  # Use the imported time class instead of datetime.time
                    
                    if descanso_inicio < visita_hora:
                        visitas_data.insert(i, rest_row)
                        inserted = True
                        break
                except (ValueError, AttributeError):
                    # If there's an error parsing the time, continue to next item
                    continue
            
            # If not inserted (rest is after all visits), append to the end
            if not inserted:
                visitas_data.append(rest_row)
        
        if len(visitas_data) > 1:
            # Adjust column widths to fit all 5 columns
            visitas_table = Table(visitas_data, colWidths=[0.5*inch, 0.5*inch, 2.5*inch, 2.5*inch, 1.5*inch])
            visitas_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.grey),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('BACKGROUND', (0,1), (-1,-1), colors.beige),
                ('GRID', (0,0), (-1,-1), 1, colors.black),
                ('ALIGN', (1,1), (2,-1), 'LEFT'), # Align address and action columns to the left
                ('LEFTPADDING', (1,1), (2,-1), 6),
            ]))
            
            # Add special styling for the rest period row if it exists
            if descanso_inicio and descanso_fin:
                # Find the rest row index
                for i in range(1, len(visitas_data)):
                    if "Descanso del conductor" in visitas_data[i][1].text:
                        # Apply special background color for the rest period row
                        visitas_table.setStyle(TableStyle([
                            ('BACKGROUND', (0,i), (-1,i), colors.wheat),
                            ('TEXTCOLOR', (0,i), (-1,i), colors.brown),
                        ]))
                        break
                        
            story.append(visitas_table)
        else:
            story.append(Paragraph("No hay visitas asignadas para esta ruta.", styles['Normal']))

        story.append(Spacer(1, 0.3*inch))

    # Add section for unattended rides (pedidos_no_atendidos)
    pedidos_no_atendidos = planificacion_data.get('pedidos_no_atendidos_procesados', []) if is_dict else getattr(planificacion_data, 'pedidos_no_atendidos_procesados', [])
    
    # Add a page break before the unattended rides section
    story.append(PageBreak())
    
    if pedidos_no_atendidos:
        story.append(Paragraph("Pedidos No Atendidos", styles['h1']))
        story.append(Spacer(1, 0.2*inch))
        
        # Split into two groups: dropped by motor vs dropped by creator
        dropped_by_motor = [p for p in pedidos_no_atendidos if not getattr(p, 'no_enviado_al_optimizador', False)]
        dropped_by_creator = [p for p in pedidos_no_atendidos if getattr(p, 'no_enviado_al_optimizador', False)]
        
        # Helper function to create dropped rides table
        def create_dropped_rides_table(pedidos_list, title):
            story.append(Paragraph(title, styles['h2']))
            story.append(Spacer(1, 0.1*inch))
            
            if not pedidos_list:
                story.append(Paragraph(f"No hay pedidos en esta categoría.", styles['Normal']))
                story.append(Spacer(1, 0.2*inch))
                return
                
            # Create table headers
            dropped_data = [[
                Paragraph("<b>ID Pedido</b>", small_style),
                Paragraph("<b>Cliente</b>", small_style),
                Paragraph("<b>Características</b>", small_style),
                Paragraph("<b>Direcciones</b>", small_style)
            ]]
            
            # Add rows for each unattended pedido
            for pedido in pedidos_list:
                # Get client info
                cliente = getattr(pedido, 'cliente', None)
                cliente_info = "No disponible"
                caracteristicas_info = "Ninguna"
                
                if cliente:
                    nombre = getattr(cliente, 'nombre', '')
                    apellido = getattr(cliente, 'apellido', '')
                    documento = getattr(cliente, 'documento', '')
                    cliente_info = f"{nombre} {apellido} (Doc: {documento})"
                    
                    # Get client characteristics
                    caracteristicas = getattr(cliente, 'caracteristicas', [])
                    if caracteristicas:
                        caracteristicas_names = [getattr(c, 'nombre', '') for c in caracteristicas]
                        caracteristicas_info = ", ".join(caracteristicas_names)
                
                # Get paradas info
                paradas = getattr(pedido, 'paradas', [])
                paradas_info = "No disponible"
                #ordernar por posicion_en_pedido
                paradas = sorted(paradas, key=lambda p: getattr(p, 'posicion_en_pedido', 0)) if paradas else []
                if paradas:
                    paradas_direcciones = [getattr(p, 'direccion', 'Sin dirección') for p in paradas]
                    paradas_info = "<br/>".join([f"- {dir}" for dir in paradas_direcciones])
                
                dropped_data.append([
                    Paragraph(str(getattr(pedido, 'id', 'N/A')), small_style),
                    Paragraph(cliente_info, small_style),
                    Paragraph(caracteristicas_info, small_style),
                    Paragraph(paradas_info, small_style)
                ])
            
            # Create the table
            dropped_table = Table(dropped_data, colWidths=[0.7*inch, 2*inch, 1.8*inch, 3*inch])
            dropped_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.grey),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('BACKGROUND', (0,1), (-1,-1), colors.beige),
                ('GRID', (0,0), (-1,-1), 1, colors.black),
                ('LEFTPADDING', (0,0), (-1,-1), 6),
            ]))
            
            story.append(dropped_table)
            story.append(Spacer(1, 0.2*inch))
        
        # Process pedidos dropped by the optimization engine
        create_dropped_rides_table(dropped_by_motor, "No Atendidos por el Optimizador")
        
        # Process pedidos dropped by the creator
        create_dropped_rides_table(dropped_by_creator, "No Enviados al Optimizador")
    else:
        story.append(Paragraph("Pedidos No Atendidos", styles['h1']))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph("No hay pedidos no atendidos en esta planificación.", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))

    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_estadisticas_pdf(planificaciones, start_date, end_date):
    """
    Genera un informe PDF con estadísticas sobre las planificaciones en un período de tiempo.
    
    Args:
        planificaciones: Lista de planificaciones a analizar
        start_date: Fecha de inicio del período (datetime)
        end_date: Fecha de fin del período (datetime)
    
    Returns:
        BytesIO: Buffer con el PDF generado
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                        leftMargin=0.5*inch, rightMargin=0.5*inch,
                        topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    custom_style = ParagraphStyle(
        'CustomStyle',
        parent=styles['Normal'],
        spaceAfter=12,
        alignment=1  # Center alignment
    )
    
    story = []
    
    # Título del informe
    title = f"Informe Estadístico de Planificaciones"
    subtitle = f"Período: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
    story.append(Paragraph(title, styles['h1']))
    story.append(Paragraph(subtitle, custom_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Recolectar datos para estadísticas
    total_pedidos_atendidos = 0
    total_pedidos_no_atendidos = 0
    tipos_parada_counter = Counter()
    datos_diarios = defaultdict(lambda: {'atendidos': 0, 'no_atendidos': 0})
    
    # Procesar planificaciones
    for plan in planificaciones:
        log.info(f"Procesando planificación {plan.id if hasattr(plan, 'id') else 'unknown'}")
        
        # Acceso seguro a la fecha
        fecha_plan = None
        if hasattr(plan, 'fecha'):
            fecha_plan = plan.fecha.date()
        elif isinstance(plan, dict) and 'fecha' in plan:
            fecha_plan = plan['fecha'].date()
        else:
            continue  # Skip if no date available
        
        # Pedidos no atendidos - acceso seguro
        pedidos_no_atendidos = []
        if hasattr(plan, 'pedidos_no_atendidos') and plan.pedidos_no_atendidos is not None:
            pedidos_no_atendidos = plan.pedidos_no_atendidos
        elif isinstance(plan, dict) and 'pedidos_no_atendidos' in plan:
            pedidos_no_atendidos = plan['pedidos_no_atendidos']
        # Fallback: __dict__ puede tener el atributo incluso si no está en el objeto
        elif hasattr(plan, '__dict__') and 'pedidos_no_atendidos' in plan.__dict__:
            pedidos_no_atendidos = plan.__dict__['pedidos_no_atendidos']
            
        num_no_atendidos = len(pedidos_no_atendidos)
        total_pedidos_no_atendidos += num_no_atendidos
        datos_diarios[fecha_plan]['no_atendidos'] += num_no_atendidos
        
        # Rutas y pedidos atendidos - acceso seguro
        rutas = []
        if hasattr(plan, 'rutas'):
            rutas = plan.rutas
        elif isinstance(plan, dict) and 'rutas' in plan:
            rutas = plan['rutas']
        elif hasattr(plan, '__dict__') and 'rutas' in plan.__dict__:
            rutas = plan.__dict__['rutas']
            
        pedidos_atendidos_set = set()  # Para evitar contar duplicados
        
        for ruta in rutas:
            # Obtener visitas con acceso seguro
            visitas = []
            if hasattr(ruta, 'visitas'):
                visitas = ruta.visitas
            elif isinstance(ruta, dict) and 'visitas' in ruta:
                visitas = ruta['visitas']
            elif hasattr(ruta, '__dict__') and 'visitas' in ruta.__dict__:
                visitas = ruta.__dict__['visitas']
                
            for visita in visitas:
                # Obtener tipo_item con acceso seguro
                tipo_item = None
                if hasattr(visita, 'tipo_item'):
                    tipo_item = visita.tipo_item
                elif isinstance(visita, dict) and 'tipo_item' in visita:
                    tipo_item = visita['tipo_item']
                elif hasattr(visita, '__dict__') and 'tipo_item' in visita.__dict__:
                    tipo_item = visita.__dict__['tipo_item']
                
                if tipo_item == model.TipoItemVisita.parada:
                    # Obtener item con acceso seguro
                    item = None
                    if hasattr(visita, 'item') and visita.item is not None:
                        item = visita.item
                    elif isinstance(visita, dict) and 'item' in visita:
                        item = visita['item']
                    elif hasattr(visita, 'parada') and visita.parada is not None:
                        item = visita.parada
                    elif hasattr(visita, '__dict__') and 'parada' in visita.__dict__:
                        item = visita.__dict__['parada']
                        
                    if item:
                        # Contar tipo de parada
                        tipo_parada_obj = None
                        if hasattr(item, 'tipo_parada') and item.tipo_parada is not None:
                            tipo_parada_obj = item.tipo_parada
                        
                        if tipo_parada_obj and hasattr(tipo_parada_obj, 'nombre'):
                            nombre_tipo = tipo_parada_obj.nombre
                            tipos_parada_counter[nombre_tipo] += 1
                        else:
                            # Fallback si no tenemos un nombre de tipo
                            tipos_parada_counter["Tipo sin nombre"] += 1
                                
                        # Contar pedido atendido (solo una vez)
                        id_pedido = None
                        if hasattr(item, 'id_pedido'):
                            id_pedido = item.id_pedido
                        elif isinstance(item, dict) and 'id_pedido' in item:
                            id_pedido = item['id_pedido']
                            
                        if id_pedido and id_pedido not in pedidos_atendidos_set:
                            pedidos_atendidos_set.add(id_pedido)
                            datos_diarios[fecha_plan]['atendidos'] += 1
                            total_pedidos_atendidos += 1
    
    # Tabla de estadísticas generales
    story.append(Paragraph("Estadísticas Generales", styles['h2']))
    
    # Datos para la tabla general
    general_data = [
        ["<b>Métrica</b>", "<b>Cantidad</b>"],
        ["Pedidos Atendidos", str(total_pedidos_atendidos)],
        ["Pedidos No Atendidos", str(total_pedidos_no_atendidos)],
        ["Total Pedidos", str(total_pedidos_atendidos + total_pedidos_no_atendidos)]
    ]
    log.info('General data: %s', general_data)
    # Crear tabla general
    general_table = Table(
        [[Paragraph(cell, styles['Normal']) for cell in row] for row in general_data],
        colWidths=[4*inch, 3*inch]
    )
    
    # Ensure colors from reportlab.lib is used
    from reportlab.lib import colors as report_colors

    general_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), report_colors.darkblue),
        ('TEXTCOLOR', (0,0), (-1,0), report_colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), report_colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 1, report_colors.black),
    ]))
    
    story.append(general_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Tabla de tipos de parada
    if tipos_parada_counter:
        story.append(Paragraph("Tipos de Paradas", styles['h2']))
        
        # Datos para la tabla de tipos de parada
        tipos_data = [["<b>Tipo de Parada</b>", "<b>Cantidad</b>"]]
        for tipo, cantidad in tipos_parada_counter.most_common():
            tipos_data.append([tipo, str(cantidad)])
        
        tipos_table = Table(
            [[Paragraph(cell, styles['Normal']) for cell in row] for row in tipos_data],
            colWidths=[4*inch, 3*inch]
        )


        tipos_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), report_colors.darkblue),
            ('TEXTCOLOR', (0,0), (-1,0), report_colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), report_colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 1, report_colors.black),
        ]))
        
        story.append(tipos_table)
        story.append(Spacer(1, 0.3*inch))
    
    # Gráfico de pedidos atendidos vs no atendidos por día
    if datos_diarios:
        story.append(Paragraph("Pedidos Atendidos vs No Atendidos por Día", styles['h2']))
        
        # Ordenar fechas
        fechas = sorted(datos_diarios.keys())
        
        # Preparar datos para el gráfico
        x = np.arange(len(fechas))
        atendidos = [datos_diarios[fecha]['atendidos'] for fecha in fechas]
        no_atendidos = [datos_diarios[fecha]['no_atendidos'] for fecha in fechas]
        
        # Crear gráfico
        plt.figure(figsize=(10, 6))
        width = 0.35
        plt.bar(x - width/2, atendidos, width, label='Atendidos', color='blue')
        plt.bar(x + width/2, no_atendidos, width, label='No Atendidos', color='red')
        
        plt.xlabel('Fecha')
        plt.ylabel('Cantidad de Pedidos')
        plt.title('Pedidos Atendidos vs No Atendidos por Día')
        plt.xticks(x, [fecha.strftime('%d/%m') for fecha in fechas], rotation=45)
        plt.legend()
        plt.tight_layout()
        
        # Guardar gráfico en memoria y añadirlo al PDF
        imgdata = BytesIO()
        plt.savefig(imgdata, format='png')
        imgdata.seek(0)
        
        img = Image(imgdata, width=6.5*inch, height=4*inch)
        story.append(img)
        story.append(Spacer(1, 0.2*inch))
        
        # Gráfico de pastel para la proporción global
        if total_pedidos_atendidos + total_pedidos_no_atendidos > 0:
            story.append(Paragraph("Proporción de Pedidos Atendidos vs No Atendidos", styles['h2']))
            
            # Crear gráfico de pastel
            plt.figure(figsize=(8, 8))
            labels = ['Atendidos', 'No Atendidos']
            sizes = [total_pedidos_atendidos, total_pedidos_no_atendidos]
            chart_colors = ['blue', 'red']  # Renamed to avoid conflict
            explode = (0.1, 0)  # explode the 1st slice (Atendidos)
            
            plt.pie(sizes, explode=explode, labels=labels, colors=chart_colors, autopct='%1.1f%%',
                    shadow=True, startangle=90)
            plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
            plt.title('Proporción de Pedidos Atendidos vs No Atendidos')
            
            # Guardar gráfico en memoria y añadirlo al PDF
            imgdata_pie = BytesIO()
            plt.savefig(imgdata_pie, format='png')
            imgdata_pie.seek(0)
            
            img_pie = Image(imgdata_pie, width=5*inch, height=5*inch)
            story.append(img_pie)
    
    # Construir el PDF
    doc.build(story)
    buffer.seek(0)
    return buffer
