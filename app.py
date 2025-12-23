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

# ================ IMPORTACIONES PARA PDF MEJORADO ================
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

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
        """, 
