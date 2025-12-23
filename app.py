import streamlit as st
import os
import zipfile
import tempfile
from pathlib import Path
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_classic.chains import RetrievalQA
import requests
import json
from datetime import datetime, timedelta
import base64
from io import BytesIO
import re
import qrcode
from PIL import Image

# ================ IMPORTACIONES PARA PDF MEJORADO ================
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics import renderPDF

# ================= CONFIGURACIÓN SEGURA =================
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")
ZIP_URL = "https://github.com/alkhimiya/mindgeekclinicdeployment/raw/refs/heads/main/mindgeekclinic_db.zip"

# ================= CONFIGURACIÓN CONOCIMIENTO ESPECIALIZADO =================
CONOCIMIENTO_ESPECIALIZADO_URL = "https://docs.google.com/document/d/1BZa1rid24RpRWU2nOOxOQYAaynWD5I7lg9FJrbvUMZg/edit?usp=drivesdk"
CONOCIMIENTO_DOWNLOAD_URL = "https://docs.google.com/document/d/1BZa1rid24RpRWU2nOOxOQYAaynWD5I7lg9FJrbvUMZg/export?format=txt"

# ================= CONFIGURACIÓN AGENDAMIENTO =================
CALENDLY_URL = "https://calendly.com/mindgeekclinic/consulta"
TERAPEUTA_NOMBRE = "Especialista MINDGEEKCLINIC"
TERAPEUTA_EMAIL = "consultas@mindgeekclinic.com"
CONSULTA_PRECIO = "$60 USD"
PAQUETE_PRECIO = "$150 USD"
TELEFONO_CONTACTO = "+1-555-123-4567"

# Verificar clave API al inicio
if not GROQ_API_KEY:
    st.error("""
    ❌ **ERROR DE CONFIGURACIÓN: GROQ_API_KEY no encontrada**
    
    **Solución:**
    1. Si estás en Streamlit Cloud: Ve a "Settings" → "Secrets" y añade:
       ```
       GROQ_API_KEY = "tu_clave_aqui"
       ```
    2. Si estás localmente: Crea `.streamlit/secrets.toml` con:
       ```
       GROQ_API_KEY = "tu_clave_aqui"
       ```
    """)
    st.stop()

# ================= BASE DE DATOS DE PACIENTES =================
def guardar_paciente(datos):
    """Guarda datos del paciente en session_state."""
    if "pacientes" not in st.session_state:
        st.session_state.pacientes = []
    
    datos["fecha"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    datos["id"] = f"MG-{datos['iniciales']}-{len(st.session_state.pacientes)+1:03d}"
    st.session_state.pacientes.append(datos)
    return datos["id"]

# ================= SISTEMA DE CONOCIMIENTO ESPECIALIZADO =================
@st.cache_data(ttl=1800)  # Cache de 30 minutos
def cargar_conocimiento_especializado():
    """Carga y cachea el conocimiento especializado desde Google Docs."""
    try:
        response = requests.get(CONOCIMIENTO_DOWNLOAD_URL, timeout=15)
        response.raise_for_status()
        return response.text
    except Exception as e:
        st.sidebar.warning(f"⚠️ No se pudo cargar conocimiento especializado: {e}")
        return ""

def buscar_conocimiento_especializado(dolencia):
    """Busca conocimiento especializado relevante para la dolencia."""
    conocimiento_texto = cargar_conocimiento_especializado()
    
    if not conocimiento_texto or not dolencia:
        return ""
    
    dolencia_lower = dolencia.lower()
    palabras_clave = [p.strip('.,;').lower() for p in dolencia_lower.split() if len(p) > 3]
    
    if not palabras_clave:
        return ""
    
    # Análisis inteligente del conocimiento
    lineas = conocimiento_texto.split('\n')
    secciones_encontradas = []
    seccion_actual = []
    capturando_seccion = False
    titulo_seccion = ""
    
    for i, linea in enumerate(lineas):
        # Detectar inicio de sección (###)
        if linea.strip().startswith('###'):
            # Guardar sección anterior si era relevante
            if capturando_seccion and seccion_actual:
                contenido_seccion = ' '.join(seccion_actual).lower()
                if any(palabra in contenido_seccion for palabra in palabras_clave):
                    secciones_encontradas.append({
                        'titulo': titulo_seccion,
                        'contenido': '\n'.join(seccion_actual),
                        'relevancia': sum(1 for palabra in palabras_clave if palabra in contenido_seccion)
                    })
            
            # Iniciar nueva sección
            titulo_seccion = linea.strip()
            seccion_actual = [linea]
            capturando_seccion = True
        
        elif capturando_seccion:
            if linea.strip():  # Ignorar líneas vacías
                seccion_actual.append(linea)
        
        # También buscar en líneas individuales para temas muy específicos
        elif any(palabra in linea.lower() for palabra in palabras_clave):
            secciones_encontradas.append({
                'titulo': f"Referencia específica: {dolencia}",
                'contenido': linea,
                'relevancia': 5  # Alta relevancia por coincidencia directa
            })
    
    # Procesar última sección
    if capturando_seccion and seccion_actual:
        contenido_seccion = ' '.join(seccion_actual).lower()
        if any(palabra in contenido_seccion for palabra in palabras_clave):
            secciones_encontradas.append({
                'titulo': titulo_seccion,
                'contenido': '\n'.join(seccion_actual),
                'relevancia': sum(1 for palabra in palabras_clave if palabra in contenido_seccion)
            })
    
    # Ordenar por relevancia y formatear resultado
    secciones_encontradas.sort(key=lambda x: x['relevancia'], reverse=True)
    
    if secciones_encontradas:
        resultado = "="*60 + "\n"
        resultado += "🎯 **CONOCIMIENTO ESPECIALIZADO APLICABLE**\n"
        resultado += "="*60 + "\n\n"
        
        for i, seccion in enumerate(secciones_encontradas[:3], 1):  # Máximo 3 secciones
            resultado += f"**{seccion['titulo']}**\n\n"
            resultado += f"{seccion['contenido']}\n"
            if i < len(secciones_encontradas[:3]):
                resultado += "\n" + "-"*40 + "\n\n"
        
        return resultado
    
    return ""

# ================= FUNCIONES PARA PROTOCOLO TERAPÉUTICO =================
def extraer_sesiones_del_diagnostico(diagnostico):
    """Extrae automáticamente las 3 sesiones del diagnóstico generado."""
    sesiones = []
    
    # Buscar patrones de sesiones en el diagnóstico
    lineas = diagnostico.split('\n')
    
    for i, linea in enumerate(lineas):
        if 'sesión' in linea.lower() and '1:' in linea.lower():
            # Tomar la sesión 1 y las siguientes 3 líneas
            sesion1 = linea
            for j in range(1, 4):
                if i + j < len(lineas):
                    sesion1 += "\n" + lineas[i + j]
            sesiones.append(sesion1[:300] + "...")
        
        elif 'sesión' in linea.lower() and '2:' in linea.lower():
            sesion2 = linea
            for j in range(1, 4):
                if i + j < len(lineas):
                    sesion2 += "\n" + lineas[i + j]
            sesiones.append(sesion2[:300] + "...")
        
        elif 'sesión' in linea.lower() and '3:' in linea.lower():
            sesion3 = linea
            for j in range(1, 4):
                if i + j < len(lineas):
                    sesion3 += "\n" + lineas[i + j]
            sesiones.append(sesion3[:300] + "...")
    
    # Si no se encontraron sesiones, crear por defecto
    if len(sesiones) < 3:
        sesiones = [
            "Sesión 1: Identificación y conciencia del conflicto emocional raíz. Trabajo en la toma de conciencia del resentir específico y su relación con los eventos identificados.",
            "Sesión 2: Reprocesamiento emocional y liberación del resentir. Uso de técnicas de hipnosis y biodescodificación para transformar la emoción almacenada.",
            "Sesión 3: Integración y protocolo de mantenimiento con autohipnosis. Consolidación de los cambios y establecimiento de prácticas diarias para prevenir recaídas."
        ]
    
    return sesiones[:3]  # Asegurar máximo 3 sesiones

def obtener_contenido_sesion(num_sesion, datos_paciente, diagnostico):
    """Devuelve contenido específico para cada sesión."""
    contenidos = {
        1: f"""
        **Objetivo:** Identificar el conflicto emocional raíz relacionado con '{datos_paciente['dolencia']}'.
        
        **Actividades:**
        1. Revisión del diagnóstico generado
        2. Identificación del resentir específico
        3. Conexión con eventos emocionales reportados
        4. Ejercicio de consciencia corporal
        
        **Material necesario:** Este documento, lápiz y papel.
        
        **Duración:** 45-60 minutos
        """,
        2: f"""
        **Objetivo:** Reprocesar la emoción almacenada y liberar el resentir.
        
        **Actividades:**
        1. Técnica de respiración consciente
        2. Visualización guiada para la liberación emocional
        3. Ejercicio de perdón (si aplica)
        4. Integración de nuevos aprendizajes
        
        **Material necesario:** Auriculares, espacio tranquilo.
        
        **Duración:** 40-50 minutos
        """,
        3: f"""
        **Objetivo:** Consolidar cambios y establecer protocolo de mantenimiento.
        
        **Actividades:**
        1. Creación de afirmaciones personalizadas
        2. Protocolo de autohipnosis diaria
        3. Plan de seguimiento emocional
        4. Identificación de señales de alerta
        
        **Material necesario:** Grabadora de voz (opcional), diario emocional.
        
        **Duración:** 30-40 minutos
        """
    }
    
    return contenidos.get(num_sesion, "Contenido de sesión no disponible.")

def obtener_ejercicio_sesion(num_sesion):
    """Devuelve ejercicio práctico para cada sesión."""
    ejercicios = {
        1: """
        **EJERCICIO: EL MAPA EMOCIONAL**
        
        1. Dibuje un círculo en el centro de una hoja, escriba su síntoma: '{dolencia}'
        2. Conecte con líneas hacia eventos emocionales identificados
        3. Para cada evento, escriba la emoción principal que sintió
        4. Marque con color la emoción más intensa
        5. Respire profundamente 3 veces observando su mapa
        
        **Reflexión:** ¿Qué patrón observa en las conexiones?
        """,
        2: """
        **EJERCICIO: LA CARTA DE LIBERACIÓN**
        
        1. Escriba una carta a la persona/situación relacionada con su conflicto
        2. Exprese todo lo que no pudo decir en su momento (sin enviarla)
        3. Lea la carta en voz alta
        4. Queme o rompa la carta simbólicamente
        5. Escriba una nueva carta de perdón hacia usted mismo
        
        **Reflexión:** ¿Cómo se siente después de este ejercicio?
        """,
        3: """
        **EJERCICIO: PROTOCOLO DIARIO DE AUTOHIPNOSIS**
        
        1. Busque un lugar tranquilo, siéntese cómodamente
        2. Cierre los ojos y respire profundamente 5 veces
        3. Repita su afirmación personal 3 veces
        4. Visualice su cuerpo sano y en equilibrio por 2 minutos
        5. Agradezca a su cuerpo por su sabiduría
        
        **Reflexión:** Practique esto cada mañana durante 21 días.
        """
    }
    
    return ejercicios.get(num_sesion, "Ejercicio no disponible.")

def generar_qr_code(url, filename="qr_code.png"):
    """Genera un código QR para URL y lo guarda temporalmente."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)
    return filename

# ================= FUNCIÓN PARA GENERAR PDF MEJORADO =================
def generar_pdf_diagnostico_completo(datos_paciente, diagnostico):
    """Genera PDF profesional con diagnóstico, protocolo y agendamiento."""
    try:
        buffer = BytesIO()
        
        # Configurar documento
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
            title=f"Diagnóstico MINDGEEKCLINIC - {datos_paciente['iniciales']}"
        )
        
        styles = getSampleStyleSheet()
        
        # Estilos personalizados
        estilo_titulo = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1E3A8A'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        estilo_subtitulo = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#374151'),
            spaceAfter=8,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        estilo_cuerpo = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#4B5563'),
            leading=14,
            alignment=TA_JUSTIFY
        )
        
        estilo_paciente = ParagraphStyle(
            'PacienteInfo',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#6B7280'),
            leading=12
        )
        
        estilo_diagnostico = ParagraphStyle(
            'Diagnostico',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#1F2937'),
            leading=13,
            alignment=TA_JUSTIFY,
            spaceAfter=6
        )
        
        estilo_sesion = ParagraphStyle(
            'SesionHeader',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#1E3A8A'),
            spaceBefore=15,
            spaceAfter=8,
            fontName='Helvetica-Bold'
        )
        
        estilo_agendamiento = ParagraphStyle(
            'Agendamiento',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#065F46'),
            leading=13,
            backColor=colors.HexColor('#D1FAE5'),
            borderPadding=10,
            spaceBefore=10,
            spaceAfter=10
        )
        
        # Preparar contenido
        story = []
        
        # ===== PORTADA MEJORADA =====
        story.append(Spacer(1, 1.5*inch))
        story.append(Paragraph("🧠 MINDGEEKCLINIC", estilo_titulo))
        story.append(Paragraph("Sistema Profesional de Biodescodificación", estilo_subtitulo))
        story.append(Spacer(1, 0.5*inch))
        
        # Información del paciente en portada
        info_portada = [
            ["<b>PACIENTE:</b>", datos_paciente['iniciales']],
            ["<b>EDAD:</b>", f"{datos_paciente['edad']} años"],
            ["<b>FECHA DE GENERACIÓN:</b>", datetime.now().strftime("%d/%m/%Y %H:%M")],
            ["<b>ID DEL DOCUMENTO:</b>", datos_paciente.get('id', f"MG-{datos_paciente['iniciales']}-{datetime.now().strftime('%Y%m%d')}")],
            ["<b>DOLENCIA PRINCIPAL:</b>", datos_paciente['dolencia'][:100] + "..." if len(datos_paciente['dolencia']) > 100 else datos_paciente['dolencia']]
        ]
        
        tabla_portada = Table(info_portada, colWidths=[2.5*inch, 4*inch])
        tabla_portada.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F3F4F6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        
        story.append(tabla_portada)
        story.append(Spacer(1, 0.3*inch))
        
        story.append(Paragraph("<i>Documento confidencial - Uso exclusivo del paciente</i>", 
                              ParagraphStyle('Confidencial', parent=styles['Normal'], fontSize=8, 
                                            textColor=colors.grey, alignment=TA_CENTER)))
        
        story.append(PageBreak())
        
        # ===== SECCIÓN 1: DATOS COMPLETOS DEL PACIENTE =====
        story.append(Paragraph("INFORMACIÓN CLÍNICA COMPLETA", estilo_titulo))
        story.append(Spacer(1, 0.25*inch))
        
        datos_completos = [
            ["<b>Estado Civil:</b>", datos_paciente['estado_civil']],
            ["<b>Situación Laboral:</b>", datos_paciente['situacion_laboral']],
            ["<b>Tensión Arterial:</b>", datos_paciente['tension']],
            ["<b>Tiempo de Padecimiento:</b>", datos_paciente['tiempo_padecimiento']],
            ["<b>Frecuencia:</b>", datos_paciente['frecuencia']],
            ["<b>Intensidad:</b>", f"{datos_paciente['intensidad']}/10"]
        ]
        
        if datos_paciente.get('diagnostico_medico') and datos_paciente['diagnostico_medico'].strip():
            datos_completos.append(["<b>Diagnóstico Médico Previo:</b>", datos_paciente['diagnostico_medico'][:200] + "..."])
        
        tabla_datos = Table(datos_completos, colWidths=[2.5*inch, 4*inch])
        tabla_datos.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        
        story.append(tabla_datos)
        story.append(Spacer(1, 0.3*inch))
        
        # Eventos emocionales
        story.append(Paragraph("EVENTOS EMOCIONALES IDENTIFICADOS", estilo_subtitulo))
        eventos_texto = datos_paciente['eventos_emocionales'][:500] + "..." if len(datos_paciente['eventos_emocionales']) > 500 else datos_paciente['eventos_emocionales']
        story.append(Paragraph(eventos_texto, estilo_cuerpo))
        
        story.append(PageBreak())
        
        # ===== SECCIÓN 2: DIAGNÓSTICO DE BIODESCODIFICACIÓN =====
        story.append(Paragraph("DIAGNÓSTICO DE BIODESCODIFICACIÓN", estilo_titulo))
        story.append(Spacer(1, 0.25*inch))
        
        # Limpiar y formatear diagnóstico para PDF
        def limpiar_texto_para_pdf(texto):
            if not texto:
                return ""
            
            # Reemplazar caracteres especiales
            texto = texto.replace('**', '').replace('__', '')
            texto = re.sub(r'<[^>]*>', '', texto)
            
            # Separar en párrafos
            parrafos = texto.split('\n')
            parrafos_limpios = []
            
            for p in parrafos:
                p = p.strip()
                if p:
                    # Capitalizar primera letra
                    if len(p) > 1:
                        p = p[0].upper() + p[1:]
                    parrafos_limpios.append(p)
            
            return '<br/>'.join(parrafos_limpios)
        
        diagnostico_limpio = limpiar_texto_para_pdf(diagnostico)
        
        if diagnostico_limpio:
            story.append(Paragraph(diagnostico_limpio, estilo_diagnostico))
        
        story.append(PageBreak())
        
        # ===== SECCIÓN 3: PROTOCOLO DE 3 SESIONES TERAPÉUTICAS =====
        story.append(Paragraph("🎯 PROTOCOLO TERAPÉUTICO DE 3 SESIONES", estilo_titulo))
        story.append(Spacer(1, 0.3*inch))
        
        story.append(Paragraph("""
        Este protocolo ha sido diseñado específicamente para usted basado en su diagnóstico. 
        Cada sesión está estructurada para trabajar progresivamente en la resolución de su conflicto emocional.
        """, estilo_cuerpo))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Extraer sesiones del diagnóstico
        sesiones = extraer_sesiones_del_diagnostico(diagnostico)
        
        for i, sesion in enumerate(sesiones, 1):
            # Encabezado de sesión
            story.append(Paragraph(f"SESIÓN {i}", estilo_sesion))
            
            # Descripción de la sesión
            story.append(Paragraph(sesion, estilo_cuerpo))
            story.append(Spacer(1, 0.2*inch))
            
            # Contenido específico
            contenido = obtener_contenido_sesion(i, datos_paciente, diagnostico)
            story.append(Paragraph("<b>Contenido detallado:</b>", estilo_subtitulo))
            story.append(Paragraph(contenido, estilo_cuerpo))
            story.append(Spacer(1, 0.2*inch))
            
            # Ejercicio práctico
            ejercicio = obtener_ejercicio_sesion(i).replace('{dolencia}', datos_paciente['dolencia'])
            story.append(Paragraph("<b>Ejercicio práctico:</b>", estilo_subtitulo))
            story.append(Paragraph(ejercicio, estilo_cuerpo))
            
            # Separador entre sesiones (excepto última)
            if i < len(sesiones):
                story.append(Spacer(1, 0.4*inch))
                story.append(Paragraph("-" * 80, ParagraphStyle('Separador', parent=styles['Normal'], 
                                                               fontSize=8, textColor=colors.grey, 
                                                               alignment=TA_CENTER)))
                story.append(Spacer(1, 0.4*inch))
        
        story.append(PageBreak())
        
        # ===== SECCIÓN 4: AGENDAMIENTO DE CONSULTA PROFESIONAL =====
        story.append(Paragraph("📅 AGENDAMIENTO DE CONSULTA PROFESIONAL", estilo_titulo))
        story.append(Spacer(1, 0.3*inch))
        
        # Generar URL personalizada para Calendly
        calendly_url = f"{CALENDLY_URL}?name={datos_paciente['iniciales']}&a1={datos_paciente.get('id', '')}"
        
        # Contenido de agendamiento
        agendamiento_texto = f"""
        <b>¿Necesita acompañamiento profesional?</b><br/><br/>
        
        Su diagnóstico ha sido generado por nuestro sistema de inteligencia artificial especializado en biodescodificación. 
        Para un trabajo terapéutico profundo y personalizado, puede agendar una consulta con nuestros especialistas.<br/><br/>
        
        <b>Modalidades disponibles:</b><br/>
        • <font color="#1E3A8A">🔗 Video-consulta individual</font> (50 minutos): {CONSULTA_PRECIO}<br/>
        • <font color="#1E3A8A">💬 Sesión de seguimiento</font> (30 minutos): $40 USD<br/>
        • <font color="#1E3A8A">📦 Paquete 3 sesiones</font> (mejor valor): {PAQUETE_PRECIO} (ahorra 20%)<br/><br/>
        
        <b>Especialista asignado:</b> {TERAPEUTA_NOMBRE}<br/>
        <b>Contacto:</b> {TERAPEUTA_EMAIL} | {TELEFONO_CONTACTO}<br/><br/>
        
        <b>Cómo agendar su consulta:</b><br/>
        1. Escanee el código QR en esta página con su teléfono<br/>
        2. O visite directamente: {CALENDLY_URL}<br/>
        3. Seleccione "Nuevo Paciente: {datos_paciente['iniciales']}"<br/>
        4. Elija la fecha y hora que mejor se adapte a su disponibilidad<br/><br/>
        
        <b>Preparación para su sesión:</b><br/>
        • Tenga a mano este documento durante la consulta<br/>
        • Prepare un espacio tranquilo, privado y con buena conexión a internet<br/>
        • Conéctese 5 minutos antes de la hora acordada<br/>
        • Prepare sus preguntas específicas<br/><br/>
        
        <b>ID de paciente para referencia:</b> {datos_paciente.get('id', 'No asignado')}<br/>
        <b>Válido hasta:</b> {(datetime.now() + timedelta(days=90)).strftime('%d/%m/%Y')}
        """
        
        story.append(Paragraph(agendamiento_texto, estilo_agendamiento))
        story.append(Spacer(1, 0.4*inch))
        
        # Generar y añadir código QR
        try:
            qr_filename = generar_qr_code(calendly_url, f"qr_{datos_paciente['iniciales']}.png")
            qr_image = ReportLabImage(qr_filename, width=1.5*inch, height=1.5*inch)
            story.append(qr_image)
            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph(f"<i>Escanee para agendar consulta con {TERAPEUTA_NOMBRE}</i>", 
                                  ParagraphStyle('QRCaption', parent=styles['Normal'], fontSize=8, 
                                                textColor=colors.grey, alignment=TA_CENTER)))
            
            # Eliminar archivo temporal
            os.remove(qr_filename)
        except Exception as e:
            story.append(Paragraph(f"URL para agendamiento: {calendly_url}", 
                                  ParagraphStyle('URLLink', parent=styles['Normal'], fontSize=9, 
                                                textColor=colors.blue)))
        
        story.append(PageBreak())
        
        # ===== SECCIÓN 5: INFORMACIÓN IMPORTANTE =====
        story.append(Paragraph("INFORMACIÓN IMPORTANTE", estilo_titulo))
        story.append(Spacer(1, 0.25*inch))
        
        info_legal = f"""
        <b>Confidencialidad:</b> Este documento contiene información confidencial del paciente. 
        Su distribución está limitada al paciente y profesionales de la salud involucrados en su tratamiento.<br/><br/>
        
        <b>Propósito del diagnóstico:</b> Este diagnóstico es una herramienta de apoyo para profesionales de salud mental 
        y no sustituye evaluación médica, diagnóstico clínico o tratamiento profesional. Siempre consulte con su médico 
        tratante antes de realizar cambios en su tratamiento.<br/><br/>
        
        <b>Uso del protocolo terapéutico:</b> Las sesiones sugeridas son guías generales. Ajuste el ritmo según 
        su comodidad y disponibilidad. Si experimenta malestar emocional significativo, detenga el ejercicio y 
        busque apoyo profesional.<br/><br/>
        
        <b>Limitación de responsabilidad:</b> MINDGEEKCLINIC proporciona herramientas de autoconocimiento y 
        acompañamiento. Los resultados pueden variar según el compromiso y circunstancias individuales.<br/><br/>
        
        <b>Contacto para emergencias:</b> Si tiene pensamientos de hacerse daño a sí mismo o a otros, 
        contacte inmediatamente a servicios de emergencia locales o líneas de ayuda en crisis.<br/><br/>
        
        <b>Fecha de generación:</b> {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}<br/>
        <b>Sistema:</b> MINDGEEKCLINIC v8.0 - Triangulación Diagnóstica con Protocolo Terapéutico<br/>
        <b>Documento ID:</b> {datos_paciente.get('id', 'No asignado')}
        """
        
        story.append(Paragraph(info_legal, ParagraphStyle('LegalText', parent=styles['Normal'], 
                                                         fontSize=9, textColor=colors.HexColor('#6B7280'),
                                                         leading=12, alignment=TA_JUSTIFY)))
        
        # ===== GENERAR PDF =====
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
        
    except Exception as e:
        st.error(f"Error al generar PDF completo: {str(e)}")
        # Fallback a PDF simple si hay error
        return generar_pdf_simple(datos_paciente, diagnostico)

def generar_pdf_simple(datos_paciente, diagnostico):
    """Función fallback si hay error en el PDF completo."""
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        story.append(Paragraph(f"Diagnóstico MINDGEEKCLINIC - {datos_paciente['iniciales']}", 
                              styles['Heading1']))
        story.append(Spacer(1, 0.5*inch))
        
        story.append(Paragraph(f"Paciente: {datos_paciente['iniciales']}", styles['Normal']))
        story.append(Paragraph(f"Edad: {datos_paciente['edad']} años", styles['Normal']))
        story.append(Paragraph(f"Dolencia: {datos_paciente['dolencia']}", styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        story.append(Paragraph("DIAGNÓSTICO:", styles['Heading2']))
        story.append(Paragraph(diagnostico[:2000] + "..." if len(diagnostico) > 2000 else diagnostico, 
                              styles['Normal']))
        
        doc.build(story)
        return buffer.getvalue()
    except:
        return None

# ================= FORMULARIO DIAGNÓSTICO =================
def formulario_diagnostico():
    """Muestra formulario clínico estructurado."""
    st.markdown("### 📋 FORMULARIO DE EVALUACIÓN CLÍNICA ESPECIALIZADA")
    
    with st.form("formulario_clinico"):
        col1, col2 = st.columns(2)
        
        with col1:
            iniciales = st.text_input("📝 **Iniciales del nombre**", max_chars=3)
            edad = st.number_input("🎂 **Edad**", min_value=1, max_value=120, value=30)
            estado_civil = st.selectbox(
                "💍 **Estado civil**",
                ["Soltero", "Casado", "Divorciado", "Viudo", "Unión libre", "Separado"]
            )
            
        with col2:
            situacion_laboral = st.selectbox(
                "💼 **Situación laboral**",
                ["Empleado", "Desempleado", "Independiente", "Estudiante", "Jubilado", "Incapacitado"]
            )
            tension_alta = st.number_input("🩺 **Tensión arterial alta (sistólica)**", 
                                          min_value=50, max_value=250, value=120)
            tension_baja = st.number_input("🩺 **Tensión arterial baja (diastólica)**",
                                          min_value=30, max_value=150, value=80)
        
        st.markdown("---")
        st.markdown("#### ⏳ **TIEMPO DEL PADECIMIENTO**")
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            tiempo_padecimiento = st.selectbox(
                "¿Desde hace cuánto tiempo siente este padecimiento?",
                ["Menos de 1 mes", "1-3 meses", "3-6 meses", "6-12 meses", 
                 "1-2 años", "2-5 años", "Más de 5 años", "Desde la infancia"]
            )
        
        with col_t2:
            frecuencia = st.selectbox(
                "¿Con qué frecuencia se presenta?",
                ["Constante", "Diariamente", "Varias veces por semana", 
                 "Semanalmente", "Mensualmente", "Ocasionalmente", "Solo en ciertas situaciones"]
            )
        
        # ===== DIAGNÓSTICO MÉDICO OPCIONAL =====
        st.markdown("---")
        st.markdown("#### 🏥 **INFORMACIÓN MÉDICA (OPCIONAL)**")
        
        diagnostico_medico = st.text_area(
            "**Diagnóstico médico recibido (si aplica):**",
            height=80,
            placeholder="Ejemplo: Diagnóstico: Gastritis crónica tipo B...",
            help="Este campo es completamente opcional."
        )
        
        st.markdown("---")
        st.markdown("#### 🎯 **EVENTOS EMOCIONALES ASOCIADOS (TRIANGULACIÓN)**")
        
        eventos_emocionales = st.text_area(
            "Describa los eventos específicos que coinciden con la aparición de los síntomas:",
            height=150,
            placeholder="Ejemplo: El síntoma empeora los lunes cuando voy a trabajar..."
        )
        
        st.markdown("---")
        st.markdown("#### 🤒 **DOLENCIA / SÍNTOMA PRINCIPAL**")
        
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            dolencia = st.text_area(
                "Describa su dolencia o síntoma principal:",
                height=120,
                placeholder="Ej: Dolor de cabeza tipo migraña, insomnio, ansiedad..."
            )
        
        with col_s2:
            intensidad = st.slider("Intensidad (1-10)", 1, 10, 5)
            factores_desencadenantes = st.text_area(
                "Factores que desencadenan o agravan los síntomas:",
                height=120,
                placeholder="Ej: Estrés laboral, discusiones, clima frío..."
            )
        
        st.markdown("---")
        st.markdown("#### 👥 **ENTORNO SOCIAL ACTUAL**")
        entorno_social = st.text_area(
            "Describa su entorno social actual y relaciones significativas:",
            height=100,
            placeholder="Ej: Vivo solo después de divorcio, tengo 2 hijos..."
        )
        
        st.markdown("---")
        submitted = st.form_submit_button(
            "🚀 **ANALIZAR CON BIODESCODIFICACIÓN Y TRIANGULACIÓN**", 
            type="primary", 
            use_container_width=True
        )
        
        if submitted:
            datos_paciente = {
                "iniciales": iniciales.upper(),
                "edad": edad,
                "estado_civil": estado_civil,
                "situacion_laboral": situacion_laboral,
                "tension": f"{tension_alta}/{tension_baja}",
                "tiempo_padecimiento": tiempo_padecimiento,
                "frecuencia": frecuencia,
                "diagnostico_medico": diagnostico_medico.strip() if diagnostico_medico else "",
                "eventos_emocionales": eventos_emocionales,
                "dolencia": dolencia,
                "intensidad": intensidad,
                "factores_desencadenantes": factores_desencadenantes,
                "entorno_social": entorno_social
            }
            
            paciente_id = guardar_paciente(datos_paciente)
            st.session_state.paciente_actual = datos_paciente
            st.session_state.mostrar_diagnostico = True
            st.rerun()

# ================= GENERAR DIAGNÓSTICO COMPLETO =================
def generar_diagnostico_triangulacion(sistema, datos_paciente):
    """Genera diagnóstico completo con triangulación y conocimiento especializado."""
    
    # Obtener conocimiento especializado relevante
    conocimiento_especializado = buscar_conocimiento_especializado(datos_paciente['dolencia'])
    
    # Preparar texto de diagnóstico médico si existe
    diagnostico_medico_texto = ""
    if datos_paciente.get('diagnostico_medico') and datos_paciente['diagnostico_medico'].strip():
        diagnostico_medico_texto = f"""
        **DIAGNÓSTICO MÉDICO PREVIO:**
        {datos_paciente['diagnostico_medico']}
        
        **INSTRUCCIÓN ESPECÍFICA:** Integrar este diagnóstico médico en el análisis de biodescodificación, 
        considerándolo como información valiosa pero analizando desde la perspectiva emocional/simbólica.
        """
    
    # Construir prompt optimizado
    prompt = f"""
    ## 🧠 DIAGNÓSTICO DE BIODESCODIFICACIÓN CON TRIANGULACIÓN Y CONOCIMIENTO ESPECIALIZADO - MINDGEEKCLINIC
    
    **DATOS COMPLETOS DEL PACIENTE:**
    - Iniciales: {datos_paciente['iniciales']}
    - Edad: {datos_paciente['edad']} años
    - Estado civil: {datos_paciente['estado_civil']}
    - Situación laboral: {datos_paciente['situacion_laboral']}
    - Tensión arterial: {datos_paciente['tension']}
    - Tiempo del padecimiento: {datos_paciente['tiempo_padecimiento']}
    - Frecuencia: {datos_paciente['frecuencia']}
    - Intensidad: {datos_paciente['intensidad']}/10
    
    {diagnostico_medico_texto}
    
    **SÍNTOMA PRINCIPAL (Foco del análisis):**
    "{datos_paciente['dolencia']}"
    
    **CONOCIMIENTO ESPECIALIZADO RELEVANTE (Integrar en el análisis):**
    {conocimiento_especializado if conocimiento_especializado else "No se encontró conocimiento especializado específico para esta dolencia."}
    
    **EVENTOS EMOCIONALES ASOCIADOS (Para triangulación diagnóstica):**
    {datos_paciente['eventos_emocionales']}
    
    **FACTORES DESENCADENANTES IDENTIFICADOS:**
    {datos_paciente['factores_desencadenantes']}
    
    **ENTORNO SOCIAL Y RELACIONAL:**
    {datos_paciente['entorno_social']}
    
    **INSTRUCCIONES ESPECÍFICAS PARA EL DIAGNÓSTICO:**
    
    1. **ANÁLISIS INTEGRADO:**
       - Combina el conocimiento de la biblioteca RAG con el conocimiento especializado proporcionado
       - Prioriza las interpretaciones más específicas y profundas cuando estén disponibles
       - Relaciona los eventos emocionales con el conocimiento especializado aplicable
    
    2. **TRIANGULACIÓN DIAGNÓSTICA:**
       - Analiza patrones entre eventos emocionales y aparición/empeoramiento de síntomas
       - Identifica el conflicto emocional PRECISO basado en la triangulación
       - Considera factores de tiempo (cuándo comenzó, frecuencia)
    
    3. **ESTRUCTURA DEL DIAGNÓSTICO (IMPORTANTE: Incluir 3 sesiones terapéuticas):**
       ### 🔍 DIAGNÓSTICO POR TRIANGULACIÓN
       [Explicar relación eventos-síntomas]
       
       ### 🎯 CONFLICTO EMOCIONAL IDENTIFICADO
       [Conflicto específico + significado biológico]
       
       ### 📊 INTEGRACIÓN DE CONOCIMIENTO ESPECIALIZADO
       [Cómo se aplica el conocimiento especializado a este caso]
       
       ### 💡 PROTOCOLO DE 3 SESIONES TERAPÉUTICAS
       **SESIÓN 1:** [Describir objetivo y enfoque específico para la primera sesión]
       **SESIÓN 2:** [Describir objetivo y trabajo emocional para la segunda sesión]
       **SESIÓN 3:** [Describir objetivo y estrategias de integración para la tercera sesión]
       
       ### 🎧 PROTOCOLO DE HIPNOSIS/AUTOHIPNOSIS
       [Instrucciones basadas en biblioteca de modelos]
    
    4. **REQUISITOS ESTRICTOS:**
       - DEBE usar la biblioteca de biodescodificación disponible
       - DEBE integrar el conocimiento especializado cuando sea relevante
       - DEBE incluir explícitamente 3 sesiones terapéuticas estructuradas
       - DEBE ser ESTRUCTURADO y PROFESIONAL
       - DEBE incluir instrucciones CONCRETAS para terapia
    
    **FORMATO DE RESPUESTA:** Usa el formato estructurado indicado arriba con encabezados claros.
    
    **COMIENZA EL DIAGNÓSTICO:**
    """
    
    try:
        respuesta = sistema.invoke({"query": prompt})
        return respuesta['result']
    except Exception as e:
        return f"Error al generar diagnóstico: {str(e)}"

# ================= GENERAR GUIÓN DE HIPNOSIS =================
def generar_guion_hipnosis(sistema, datos_paciente, tipo="terapeuta"):
    """Genera guión específico de hipnosis basado en biblioteca."""
    
    tipo_texto = "para aplicación por terapeuta" if tipo == "terapeuta" else "para grabación de autohipnosis"
    
    prompt = f"""
    ## 🎧 GUION DE HIPNOSIS ESPECÍFICO - MINDGEEKCLINIC
    
    **CONTEXTO DEL PACIENTE:**
    - Síntoma: {datos_paciente['dolencia']}
    - Eventos emocionales: {datos_paciente['eventos_emocionales'][:200]}
    
    **INSTRUCCIONES:**
    Generar un guión COMPLETO de hipnosis {tipo_texto} basado en la biblioteca de modelos de hipnosis.
    
    **ESTRUCTURA REQUERIDA:**
    
    ### 🎯 OBJETIVO TERAPÉUTICO
    [Objetivo específico]
    
    ### 📝 GUIÓN COMPLETO
    
    **INDUCCIÓN:**
    [Texto completo de inducción hipnótica]
    
    **TRABAJO TERAPÉUTICO:**
    [Instrucciones para trabajar el conflicto]
    
    **SUGERENCIAS POSHIPNÓTICAS:**
    [Sugerencias para después de la sesión]
    
    **DESPERTAR:**
    [Instrucciones para finalizar]
    
    ### 🕒 INSTRUCCIONES DE APLICACIÓN
    [Instrucciones específicas para {'terapeuta' if tipo == 'terapeuta' else 'paciente'}]
    
    **GUIÓN COMPLETO:**
    """
    
    try:
        respuesta = sistema.invoke({"query": prompt})
        return respuesta['result']
    except Exception as e:
        return f"Error al generar guión: {str(e)}"

# ================= SISTEMA PRINCIPAL =================
@st.cache_resource
def cargar_sistema_completo():
    """Carga el sistema RAG con biblioteca especializada."""
    
    if not GROQ_API_KEY:
        st.error("❌ GROQ_API_KEY no configurada. Verifica tus Secrets.")
        return None
    
    with st.spinner("🔄 Cargando sistema especializado..."):
        try:
            response = requests.get(ZIP_URL, stream=True, timeout=60)
            if response.status_code != 200:
                st.error(f"❌ Error al descargar biblioteca.")
                return None
            
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "biblioteca.zip")
            extract_path = os.path.join(temp_dir, "biodescodificacion_db")
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            vector_store = Chroma(persist_directory=extract_path, embedding_function=embeddings)
            
            llm = ChatGroq(
                groq_api_key=GROQ_API_KEY,
                model_name="meta-llama/llama-4-scout-17b-16e-instruct",
                temperature=0.3,
                max_tokens=4000  # Aumentado para incluir 3 sesiones
            )
            
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=vector_store.as_retriever(search_kwargs={"k": 10}),
                return_source_documents=True,
                verbose=False
            )
            
            return qa_chain
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)[:150]}")
            return None

# ================= INTERFAZ PRINCIPAL =================
st.set_page_config(
    page_title="MINDGEEKCLINIC - Biodescodificación con Protocolo Terapéutico",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/271/271226.png", width=80)
    st.markdown("### 🏥 MINDGEEKCLINIC")
    st.markdown("**Sistema con Protocolo Terapéutico**")
    st.markdown("---")
    
    st.markdown("#### 📊 Estadísticas")
    if "pacientes" in st.session_state:
        st.metric("Pacientes atendidos", len(st.session_state.pacientes))
    
    # Estado del conocimiento especializado
    st.markdown("#### 📚 Estado del Sistema")
    conocimiento_cargado = cargar_conocimiento_especializado()
    if conocimiento_cargado:
        st.success("✅ Conocimiento especializado cargado")
    else:
        st.warning("⚠️ Conocimiento especializado no disponible")
    
    # Información de agendamiento
    st.markdown("#### 📅 Agendar Consulta")
    st.info(f"""
    **Consultas profesionales:**
    • Individual: {CONSULTA_PRECIO}
    • Paquete 3: {PAQUETE_PRECIO}
    
    [Agendar ahora]({CALENDLY_URL})
    """)
    
    st.markdown("---")
    
    if st.button("🆕 Nuevo Diagnóstico", use_container_width=True, type="primary"):
        st.session_state.mostrar_diagnostico = False
        st.session_state.generar_guion = False
        st.session_state.generar_grabacion = False
        st.session_state.pdf_generado = None
        st.session_state.diagnostico_completo = None
        st.rerun()
    
    if st.button("🔄 Recargar Conocimiento", use_container_width=True):
        st.cache_data.clear()
        st.success("Conocimiento recargado")
        st.rerun()
    
    st.markdown("---")
    st.caption("🎯 Sistema con Triangulación y Protocolo Terapéutico")

# Título principal
st.title("🧠 MINDGEEKCLINIC")
st.markdown("### **Sistema de Diagnóstico con Protocolo Terapéutico y Agendamiento**")
st.markdown("*Diagnósticos enriquecidos + 3 sesiones estructuradas + Consulta profesional*")
st.markdown("---")

# Inicializar estados
if "mostrar_diagnostico" not in st.session_state:
    st.session_state.mostrar_diagnostico = False
if "paciente_actual" not in st.session_state:
    st.session_state.paciente_actual = None
if "generar_guion" not in st.session_state:
    st.session_state.generar_guion = False
if "generar_grabacion" not in st.session_state:
    st.session_state.generar_grabacion = False
if "diagnostico_completo" not in st.session_state:
    st.session_state.diagnostico_completo = None
if "pdf_generado" not in st.session_state:
    st.session_state.pdf_generado = None

# Cargar sistema
sistema = cargar_sistema_completo()

if not sistema:
    st.error("⚠️ Sistema no disponible. Verifica configuración.")
    st.stop()

# Mostrar formulario o diagnóstico
if not st.session_state.mostrar_diagnostico:
    formulario_diagnostico()
else:
    paciente = st.session_state.paciente_actual
    
    # Mostrar datos del paciente
    st.markdown(f"### 📄 **PACIENTE:** {paciente['iniciales']} • {paciente['edad']} años • ID: {paciente.get('id', 'No asignado')}")
    
    with st.expander("📋 Ver datos completos con triangulación"):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Estado civil:** {paciente['estado_civil']}")
            st.write(f"**Situación laboral:** {paciente['situacion_laboral']}")
            st.write(f"**Tiempo padecimiento:** {paciente['tiempo_padecimiento']}")
            st.write(f"**Frecuencia:** {paciente['frecuencia']}")
            st.write(f"**Intensidad:** {paciente['intensidad']}/10")
        
        with col2:
            st.write(f"**Tensión arterial:** {paciente['tension']}")
            st.write(f"**Dolencia:** {paciente['dolencia']}")
            if paciente.get('diagnostico_medico') and paciente['diagnostico_medico'].strip():
                st.write(f"**Diagnóstico médico:** {paciente['diagnostico_medico']}")
            st.write(f"**Factores desencadenantes:** {paciente['factores_desencadenantes'][:150]}...")
        
        st.markdown("#### 🎯 **Eventos Emocionales para Triangulación:**")
        st.info(paciente['eventos_emocionales'])
    
    # Mostrar conocimiento especializado aplicable (si existe)
    conocimiento_aplicable = buscar_conocimiento_especializado(paciente['dolencia'])
    if conocimiento_aplicable:
        with st.expander("🔬 **Conocimiento Especializado Aplicable**", expanded=True):
            st.markdown(conocimiento_aplicable)
    
    # Generar diagnóstico con triangulación
    st.markdown("---")
    st.markdown("### 🔬 **DIAGNÓSTICO CON PROTOCOLO DE 3 SESIONES**")
    
    if st.session_state.diagnostico_completo is None:
        with st.spinner("🔄 Generando diagnóstico con protocolo terapéutico..."):
            diagnostico = generar_diagnostico_triangulacion(sistema, paciente)
            st.session_state.diagnostico_completo = diagnostico
    
    # Mostrar diagnóstico
    st.markdown(st.session_state.diagnostico_completo)
    
    # ==== SECCIÓN DE AGENDAMIENTO MEJORADA ====
    st.markdown("---")
    st.markdown("### 📅 **CONSULTA PROFESIONAL POR VIDEOLLAMADA**")
    
    col_consulta1, col_consulta2, col_consulta3 = st.columns(3)
    
    with col_consulta1:
        st.markdown("#### 💼 **Consulta Individual**")
        st.info(f"""
        **50 minutos**
        {CONSULTA_PRECIO}
        
        • Diagnóstico profundo
        • Protocolo personalizado
        • Técnicas específicas
        • Seguimiento por email
        """)
        
        if st.button("📅 Agendar Individual", key="individual", use_container_width=True):
            st.markdown(f"[Abrir calendario de agendamiento]({CALENDLY_URL})")
    
    with col_consulta2:
        st.markdown("#### 📦 **Paquete 3 Sesiones**")
        st.success(f"""
        **Mejor valor**
        {PAQUETE_PRECIO}
        
        • 3 sesiones de 50 min
        • Ahorra 20%
        • Material completo
        • Soporte prioritario
        • Protocolo avanzado
        """)
        
        if st.button("🎯 Agendar Paquete", key="paquete", use_container_width=True, type="primary"):
            st.markdown(f"[Abrir calendario para paquete]({CALENDLY_URL}?event_type=paquete)")
    
    with col_consulta3:
        st.markdown("#### 📞 **Información de Contacto**")
        st.info(f"""
        **Especialista:**
        {TERAPEUTA_NOMBRE}
        
        **Contacto:**
        📧 {TERAPEUTA_EMAIL}
        📱 {TELEFONO_CONTACTO}
        
        **Horario:**
        Lunes a Viernes
        9:00 - 18:00 hrs
        """)
    
    # ==== SECCIÓN DE HIPNOSIS ====
    st.markdown("---")
    st.markdown("### 🎧 **PROTOCOLOS DE HIPNOSIS ESPECÍFICOS**")
    
    if not st.session_state.generar_guion and not st.session_state.generar_grabacion:
        col_hip1, col_hip2 = st.columns(2)
        
        with col_hip1:
            st.markdown("#### 👨‍⚕️ **Para aplicación por terapeuta:**")
            st.info("Basado en biblioteca de modelos de hipnosis")
            
            if st.button("📝 Generar guión COMPLETO para terapeuta", use_container_width=True):
                st.session_state.generar_guion = True
                st.rerun()
        
        with col_hip2:
            st.markdown("#### 🎵 **Para autohipnosis (grabación personal):**")
            st.info("Instrucciones específicas de la biblioteca")
            
            if st.button("🎤 Generar guión para GRABACIÓN", use_container_width=True):
                st.session_state.generar_grabacion = True
                st.rerun()
    
    # Generar guiones específicos
    if st.session_state.generar_guion:
        st.markdown("---")
        st.markdown("### 👨‍⚕️ **GUIÓN COMPLETO PARA TERAPEUTA**")
        with st.spinner("Generando guión basado en biblioteca..."):
            guion = generar_guion_hipnosis(sistema, paciente, "terapeuta")
            st.markdown(guion)
            
            if st.button("↩️ Volver a opciones", use_container_width=True):
                st.session_state.generar_guion = False
                st.rerun()
    
    if st.session_state.generar_grabacion:
        st.markdown("---")
        st.markdown("### 🎵 **GUIÓN PARA GRABACIÓN DE AUTOHIPNOSIS**")
        with st.spinner("Generando guión para grabación..."):
            guion = generar_guion_hipnosis(sistema, paciente, "grabacion")
            st.markdown(guion)
            
            st.markdown("---")
            st.markdown("#### 📋 **INSTRUCCIONES PARA GRABACIÓN:**")
            st.success("""
            1. **Preparación:** Ambiente tranquilo, sin interrupciones
            2. **Equipo:** Usar micrófono de buena calidad
            3. **Voz:** Hablar lentamente, con tono calmado
            4. **Guardar:** Nombrar archivo claramente
            5. **Uso:** Escuchar con auriculares, posición cómoda
            """)
            
            if st.button("↩️ Volver a opciones", use_container_width=True):
                st.session_state.generar_grabacion = False
                st.rerun()
    
    # ===== BOTÓN DE GUARDAR COMO PDF MEJORADO =====
    st.markdown("---")
    st.markdown("### 💾 **DESCARGAR DOCUMENTO COMPLETO**")
    
    col_pdf1, col_pdf2, col_pdf3 = st.columns([2, 1, 1])
    
    with col_pdf1:
        st.markdown("#### 📄 **PDF con Protocolo Completo**")
        st.info("""
        Incluye:
        • Diagnóstico completo
        • 3 sesiones terapéuticas detalladas
        • Ejercicios prácticos por sesión
        • Información de agendamiento
        • Código QR para consulta
        • Instrucciones profesionales
        """)
    
    with col_pdf2:
        if st.button("📦 Descargar PDF Completo", use_container_width=True, type="primary"):
            with st.spinner("🔄 Generando documento profesional..."):
                if st.session_state.paciente_actual and st.session_state.diagnostico_completo:
                    pdf_bytes = generar_pdf_diagnostico_completo(
                        st.session_state.paciente_actual,
                        st.session_state.diagnostico_completo
                    )
                    
                    if pdf_bytes:
                        st.session_state.pdf_generado = pdf_bytes
                        st.success("✅ PDF generado correctamente")
                        
                        nombre_archivo = f"MINDGEEKCLINIC_{paciente['iniciales']}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                        
                        b64 = base64.b64encode(pdf_bytes).decode()
                        href = f'<a href="data:application/pdf;base64,{b64}" download="{nombre_archivo}" target="_blank">'
                        href += '<button style="background-color: #4CAF50; color: white; padding: 14px 28px; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; width: 100%; font-weight: bold;">📥 Descargar PDF Completo</button>'
                        href += '</a>'
                        
                        st.markdown(href, unsafe_allow_html=True)
                        
                        st.info(f"""
                        **Documento listo:**
                        • {nombre_archivo}
                        • {len(pdf_bytes) / 1024:.1f} KB
                        • Imprimible en casa/imprenta
                        • Válido por 90 días
                        """)
                    else:
                        st.error("❌ Error al generar el PDF")
                else:
                    st.warning("⚠️ No hay diagnóstico para generar PDF")
    
    with col_pdf3:
        if st.button("🆕 Nuevo Diagnóstico", use_container_width=True):
            st.session_state.mostrar_diagnostico = False
            st.session_state.diagnostico_completo = None
            st.session_state.generar_guion = False
            st.session_state.generar_grabacion = False
            st.session_state.pdf_generado = None
            st.rerun()

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.8em;'>
    🧠 <b>MINDGEEKCLINIC v8.0</b> • Sistema con Protocolo Terapéutico • 
    Agendamiento Profesional • Compatible con móvil y computador • 
    <a href="{CALENDLY_URL}" style="color: #1E3A8A; text-decoration: none;">📅 Agendar Consulta</a>
    </div>
    """.format(CALENDLY_URL=CALENDLY_URL),
    unsafe_allow_html=True
)
