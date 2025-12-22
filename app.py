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
from datetime import datetime

# ================ NUEVAS IMPORTACIONES PARA PDF ================
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import base64
from io import BytesIO

# ================= CONFIGURACIÓN =================
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")
ZIP_URL = "https://github.com/alkhimiya/mindgeekclinicdeployment/raw/refs/heads/main/mindgeekclinic_db.zip"

# ================= FUNCIÓN PARA GENERAR PDF =================
def generar_pdf_diagnostico(datos_paciente, diagnostico):
    """
    Genera un PDF profesional con el diagnóstico completo.
    Retorna el PDF como bytes para descarga.
    """
    try:
        # Crear buffer para el PDF
        buffer = BytesIO()
        
        # Configurar documento
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        
        # Estilos personalizados
        estilo_titulo = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1E3A8A'),
            spaceAfter=12,
            alignment=TA_CENTER
        )
        
        estilo_subtitulo = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#374151'),
            spaceAfter=8,
            spaceBefore=12
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
        
        # Contenido del PDF
        story = []
        
        # ===== PORTADA =====
        story.append(Spacer(1, 2*inch))
        
        # Logo/Icono
        story.append(Paragraph(
            "🧠",
            ParagraphStyle(
                'Logo',
                parent=styles['Heading1'],
                fontSize=48,
                alignment=TA_CENTER
            )
        ))
        
        story.append(Spacer(1, 0.5*inch))
        
        # Título principal
        story.append(Paragraph(
            "MINDGEEKCLINIC",
            ParagraphStyle(
                'MainTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1E3A8A'),
                alignment=TA_CENTER
            )
        ))
        
        story.append(Paragraph(
            "Sistema Profesional de Biodescodificación",
            ParagraphStyle(
                'Subtitle',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#6B7280'),
                alignment=TA_CENTER
            )
        ))
        
        story.append(Spacer(1, inch))
        
        # Información del paciente en portada
        info_paciente = [
            ["<b>PACIENTE:</b>", datos_paciente['iniciales']],
            ["<b>EDAD:</b>", f"{datos_paciente['edad']} años"],
            ["<b>FECHA:</b>", datetime.now().strftime("%d/%m/%Y %H:%M")],
            ["<b>ID:</b>", f"MG-{datos_paciente['iniciales']}-{datetime.now().strftime('%Y%m%d')}"]
        ]
        
        # Crear tabla para información
        paciente_table = Table(info_paciente, colWidths=[2*inch, 3*inch])
        paciente_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F3F4F6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        
        story.append(paciente_table)
        story.append(PageBreak())
        
        # ===== SECCIÓN 1: DATOS DEL PACIENTE =====
        story.append(Paragraph("INFORMACIÓN DEL PACIENTE", estilo_titulo))
        story.append(Spacer(1, 0.25*inch))
        
        # Datos básicos en tabla
        datos_basicos = [
            ["<b>Estado Civil:</b>", datos_paciente['estado_civil']],
            ["<b>Situación Laboral:</b>", datos_paciente['situacion_laboral']],
            ["<b>Tensión Arterial:</b>", datos_paciente['tension']],
            ["<b>Tiempo Padecimiento:</b>", datos_paciente['tiempo_padecimiento']],
            ["<b>Frecuencia:</b>", datos_paciente['frecuencia']],
            ["<b>Intensidad:</b>", f"{datos_paciente['intensidad']}/10"]
        ]
        
        tabla_datos = Table(datos_basicos, colWidths=[2.5*inch, 4*inch])
        tabla_datos.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        
        story.append(tabla_datos)
        story.append(Spacer(1, 0.3*inch))
        
        # Dolencia principal
        story.append(Paragraph("DOLENCIA PRINCIPAL", estilo_subtitulo))
        story.append(Paragraph(datos_paciente['dolencia'], estilo_cuerpo))
        story.append(Spacer(1, 0.2*inch))
        
        # Factores desencadenantes
        if datos_paciente.get('factores_desencadenantes'):
            story.append(Paragraph("FACTORES DESENCADENANTES", estilo_subtitulo))
            story.append(Paragraph(datos_paciente['factores_desencadenantes'], estilo_cuerpo))
            story.append(Spacer(1, 0.2*inch))
        
        # Eventos emocionales
        story.append(Paragraph("EVENTOS EMOCIONALES ASOCIADOS", estilo_subtitulo))
        story.append(Paragraph(datos_paciente['eventos_emocionales'], estilo_cuerpo))
        story.append(Spacer(1, 0.2*inch))
        
        # Entorno social
        story.append(Paragraph("ENTORNO SOCIAL", estilo_subtitulo))
        story.append(Paragraph(datos_paciente['entorno_social'], estilo_cuerpo))
        
        story.append(PageBreak())
        
        # ===== SECCIÓN 2: DIAGNÓSTICO =====
        story.append(Paragraph("DIAGNÓSTICO DE BIODESCODIFICACIÓN", estilo_titulo))
        story.append(Spacer(1, 0.25*inch))
        
        # Dividir el diagnóstico en secciones
        diagnostico_texto = diagnostico
        
        # Limpiar y formatear el diagnóstico
        lineas = diagnostico_texto.split('\n')
        for linea in lineas:
            linea = linea.strip()
            if not linea:
                continue
                
            # Detectar títulos
            if linea.startswith('### ') or linea.startswith('## ') or linea.startswith('# '):
                # Es un título
                nivel = linea.count('#')
                texto_titulo = linea.replace('#', '').strip()
                
                if nivel == 1:  # Título principal
                    story.append(Paragraph(texto_titulo, estilo_subtitulo))
                elif nivel == 2:  # Subtítulo
                    story.append(Paragraph(
                        f"<b>{texto_titulo}</b>",
                        ParagraphStyle(
                            'SubSection',
                            parent=styles['Normal'],
                            fontSize=11,
                            textColor=colors.HexColor('#1E3A8A'),
                            spaceBefore=12,
                            spaceAfter=6
                        )
                    ))
                elif nivel == 3:  # Sub-subtítulo
                    story.append(Paragraph(
                        f"<i>{texto_titulo}</i>",
                        ParagraphStyle(
                            'SubSubSection',
                            parent=styles['Normal'],
                            fontSize=10,
                            textColor=colors.HexColor('#4B5563'),
                            spaceBefore=8,
                            spaceAfter=4
                        )
                    ))
            else:
                # Es texto normal
                if '**' in linea or '__' in linea:
                    # Texto con negrita
                    linea = linea.replace('**', '<b>').replace('__', '<b>')
                    # Cerrar tags (simplificado)
                    if linea.count('<b>') % 2 != 0:
                        linea += '</b>'
                
                story.append(Paragraph(linea, estilo_diagnostico))
        
        story.append(Spacer(1, 0.3*inch))
        
        # ===== SECCIÓN 3: INFORMACIÓN DE CONTACTO Y LEGAL =====
        story.append(Paragraph("INFORMACIÓN IMPORTANTE", estilo_subtitulo))
        
        legal_text = """
        <b>Confidencialidad:</b> Este documento contiene información confidencial del paciente. 
        Su distribución está limitada al paciente y profesionales de la salud involucrados en su tratamiento.
        
        <b>Propósito:</b> Este diagnóstico es una herramienta de apoyo para profesionales de salud mental 
        y no sustituye evaluación médica, diagnóstico clínico o tratamiento profesional.
        
        <b>Contacto:</b> Para consultas profesionales, contacte a través del sistema MINDGEEKCLINIC.
        
        <b>Fecha de generación:</b> {}
        
        <b>Sistema:</b> MINDGEEKCLINIC v6.0 - Triangulación Diagnóstica
        """.format(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        
        story.append(Paragraph(legal_text, estilo_paciente))
        
        # ===== GENERAR PDF =====
        doc.build(story)
        
        # Obtener bytes del PDF
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
        
    except Exception as e:
        st.error(f"Error al generar PDF: {str(e)}")
        return None

def crear_boton_descarga_pdf(pdf_bytes, nombre_archivo):
    """
    Crea un botón de descarga para el PDF.
    """
    if pdf_bytes:
        b64 = base64.b64encode(pdf_bytes).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="{nombre_archivo}" style="text-decoration: none;">'
        href += f'<button style="background-color: #4CAF50; color: white; padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; width: 100%;">📥 Descargar PDF</button>'
        href += '</a>'
        return href
    return None

# ================= BASE DE DATOS DE PACIENTES =================
def guardar_paciente(datos):
    """Guarda datos del paciente en session_state."""
    if "pacientes" not in st.session_state:
        st.session_state.pacientes = []
    
    datos["fecha"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    datos["id"] = f"{datos['iniciales']}_{len(st.session_state.pacientes)+1:03d}"
    st.session_state.pacientes.append(datos)
    return datos["id"]

# ================= FORMULARIO DIAGNÓSTICO MEJORADO =================
def formulario_diagnostico():
    """Muestra formulario clínico estructurado CON PREGUNTAS ESPECÍFICAS."""
    st.markdown("### 📋 FORMULARIO DE EVALUACIÓN CLÍNICA ESPECIALIZADA")
    
    with st.form("formulario_clinico"):
        col1, col2 = st.columns(2)
        
        with col1:
            iniciales = st.text_input("📝 **Iniciales del nombre**", max_chars=3, 
                                     help="Ej: JPG para Juan Pérez García")
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
        
        # ==== PREGUNTAS ESPECÍFICAS NUEVAS ====
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
        
        # ==== EVENTOS EMOCIONALES DETALLADOS ====
        st.markdown("---")
        st.markdown("#### 🎯 **EVENTOS EMOCIONALES ASOCIADOS (TRIANGULACIÓN)**")
        
        st.markdown("**Pregunta clave:** ¿Qué eventos suceden en su vida que impactan emocionalmente CUANDO se presenta el cuadro?")
        
        eventos_emocionales = st.text_area(
            "Describa los eventos específicos (pasados o presentes) que coinciden con la aparición/worsening de los síntomas:",
            height=150,
            placeholder="""Ejemplo detallado:
1. El síntoma empeora los lunes cuando voy a trabajar (evento: regreso laboral)
2. Aparece después de discusiones con mi pareja (evento: conflicto relacional)
3. Se intensifica cuando visito a mis padres (evento: encuentro familiar)
4. Mejora cuando estoy de vacaciones (evento: descanso/ocio)
5. Comenzó después de la muerte de mi padre hace 2 años (evento: duelo)

Describa la RELACIÓN TEMPORAL entre eventos y síntomas:"""
        )
        
        # ==== SÍNTOMAS Y CONTEXTO ====
        st.markdown("---")
        st.markdown("#### 🤒 **DOLENCIA / SÍNTOMA PRINCIPAL**")
        
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            dolencia = st.text_area(
                "Describa su dolencia o síntoma principal:",
                height=120,
                placeholder="Ej: Dolor de cabeza tipo migraña, insomnio, ansiedad, labios quebradizos..."
            )
        
        with col_s2:
            intensidad = st.slider("Intensidad (1-10)", 1, 10, 5)
            factores_desencadenantes = st.text_area(
                "Factores que desencadenan o agravan los síntomas:",
                height=120,
                placeholder="Ej: Estrés laboral, discusiones, clima frío, ciertos alimentos..."
            )
        
        # ==== ENTORNO SOCIAL ====
        st.markdown("---")
        st.markdown("#### 👥 **ENTORNO SOCIAL ACTUAL**")
        entorno_social = st.text_area(
            "Describa su entorno social actual y relaciones significativas:",
            height=100,
            placeholder="Ej: Vivo solo después de divorcio, tengo 2 hijos que veo fines de semana, pocos amigos cercanos, relación conflictiva con jefe..."
        )
        
        # Submit
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

# ================= GENERAR DIAGNÓSTICO CON TRIANGULACIÓN =================
def generar_diagnostico_triangulacion(sistema, datos_paciente):
    """Genera diagnóstico completo con triangulación de eventos emocionales."""
    
    prompt = f"""
    ## 🧠 DIAGNÓSTICO DE BIODESCODIFICACIÓN CON TRIANGULACIÓN - MINDGEEKCLINIC
    
    **DATOS COMPLETOS DEL PACIENTE:**
    - Iniciales: {datos_paciente['iniciales']}
    - Edad: {datos_paciente['edad']} años
    - Estado civil: {datos_paciente['estado_civil']}
    - Situación laboral: {datos_paciente['situacion_laboral']}
    - Tensión arterial: {datos_paciente['tension']}
    - Tiempo del padecimiento: {datos_paciente['tiempo_padecimiento']}
    - Frecuencia: {datos_paciente['frecuencia']}
    - Intensidad: {datos_paciente['intensidad']}/10
    
    **SÍNTOMA PRINCIPAL:**
    {datos_paciente['dolencia']}
    
    **EVENTOS EMOCIONALES ASOCIADOS (PARA TRIANGULACIÓN):**
    {datos_paciente['eventos_emocionales']}
    
    **FACTORES DESENCADENANTES:**
    {datos_paciente['factores_desencadenantes']}
    
    **ENTORNO SOCIAL:**
    {datos_paciente['entorno_social']}
    
    **INSTRUCCIONES ESPECÍFICAS PARA EL ASISTENTE ESPECIALIZADO:**
    
    1. **TRIANGULACIÓN DIAGNÓSTICA:**
       - Analizar la relación TEMPORAL entre eventos emocionales y síntomas
       - Identificar PATRONES específicos en "{datos_paciente['eventos_emocionales']}"
       - Determinar si hay eventos DESENCADENANTES, MANTENEDORES o AGRAVANTES
       - Relacionar tiempo "{datos_paciente['tiempo_padecimiento']}" con eventos de vida
    
    2. **DIAGNÓSTICO DE BIODESCODIFICACIÓN ESPECÍFICO:**
       - Interpretar "{datos_paciente['dolencia']}" según biodescodificación
       - Identificar el CONFLICTO EMOCIONAL PRECISO basado en triangulación
       - Explicar SIGNIFICADO BIOLÓGICO del síntoma
       - Relacionar con e
