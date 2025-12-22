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
       - Relacionar con eventos específicos mencionados
    
    3. **PROTOCOLO TERAPÉUTICO ESTRUCTURADO (3 SESIONES):**
       - SESIÓN 1: Enfoque en [conflicto específico identificado por triangulación]
       - SESIÓN 2: Trabajo en [eventos emocionales clave identificados]
       - SESIÓN 3: Integración y [estrategias específicas basadas en factores desencadenantes]
    
    4. **PROTOCOLO DE HIPNOSIS ESPECÍFICO (basado en biblioteca de modelos):**
       - Frecuencia: 3 veces por semana (como indica biblioteca)
       - Duración: 15-20 minutos por sesión
       - Técnicas ESPECÍFICAS de la biblioteca de modelos de hipnosis
       - INSTRUCCIONES DETALLADAS para grabación o aplicación
    
    5. **RECOMENDACIONES PERSONALIZADAS:**
       - Actividades de autohipnosis DIARIAS basadas en triangulación
       - Ejercicios emocionales ESPECÍFICOS para eventos identificados
       - Estrategias para manejar factores desencadenantes
    
    **REQUISITOS ESTRICTOS DE RESPUESTA:**
    1. DEBE basarse en la biblioteca de biodescodificación disponible
    2. DEBE usar modelos de hipnosis de la biblioteca
    3. DEBE incluir INSTRUCCIONES ESPECÍFICAS para terapia
    4. DEBE mencionar técnicas CONCRETAS de la biblioteca
    5. DEBE ser ESTRUCTURADO y PROFESIONAL
    
    **FORMATO DE RESPUESTA:**
    
    ## 🔍 DIAGNÓSTICO POR TRIANGULACIÓN
    
    ### 1. Análisis de Patrones Identificados
    [Explicar relación eventos-síntomas]
    
    ### 2. Diagnóstico de Biodescodificación
    [Conflicto emocional específico + significado biológico]
    
    ### 3. Protocolo de 3 Sesiones Terapéuticas
    **Sesión 1:** [Instrucciones específicas]
    **Sesión 2:** [Instrucciones específicas]  
    **Sesión 3:** [Instrucciones específicas]
    
    ### 4. Protocolo de Hipnosis/Autohipnosis
    [Instrucciones DETALLADAS para grabación o aplicación]
    
    ### 5. Recomendaciones Específicas
    [Basadas en triangulación de eventos]
    
    **RESPUESTA PROFESIONAL ESTRUCTURADA:**
    """
    
    try:
        respuesta = sistema.invoke({"query": prompt})
        return respuesta['result']
    except Exception as e:
        return f"Error al generar diagnóstico: {str(e)}"

# ================= GENERAR GUIÓN DE HIPNOSIS (CORREGIDO) =================
def generar_guion_hipnosis(sistema, datos_paciente, tipo="terapeuta"):
    """Genera guión específico de hipnosis basado en biblioteca."""
    
    tipo_texto = "para aplicación por terapeuta" if tipo == "terapeuta" else "para grabación de autohipnosis"
    
    prompt = f"""
    ## 🎧 GUION DE HIPNOSIS ESPECÍFICO - MINDGEEKCLINIC
    
    **CONTEXTO DEL PACIENTE:**
    - Síntoma: {datos_paciente['dolencia']}
    - Conflicto identificado: [Basado en triangulación anterior]
    - Eventos emocionales: {datos_paciente['eventos_emocionales'][:200]}
    
    **INSTRUCCIONES PARA EL ASISTENTE:**
    
    Generar un guión COMPLETO de hipnosis {tipo_texto} basado en la biblioteca de modelos de hipnosis.
    
    **REQUISITOS:**
    1. Usar técnicas ESPECÍFICAS de la biblioteca de modelos
    2. Incluir inducción, trabajo terapéutico y despertar
    3. Duración: 15-20 minutos
    4. Frecuencia: 3 veces por semana
    5. Instrucciones PRECISAS para {'el terapeuta' if tipo == 'terapeuta' else 'grabación'}
    
    **ESTRUCTURA DEL GUIÓN:**
    
    ### 🎯 OBJETIVO TERAPÉUTICO
    [Objetivo específico basado en triangulación]
    
    ### 📝 GUIÓN COMPLETO
    
    **INDUCCIÓN:**
    [Texto completo de inducción hipnótica]
    
    **TRABAJO TERAPÉUTICO:**
    [Instrucciones específicas para trabajar el conflicto]
    
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
        st.error("❌ Configura GROQ_API_KEY en Streamlit Secrets.")
        return None
    
    with st.spinner("🔄 Cargando sistema especializado..."):
        try:
            # Descargar biblioteca
            response = requests.get(ZIP_URL, stream=True, timeout=60)
            if response.status_code != 200:
                st.error(f"❌ Error al descargar biblioteca.")
                return None
            
            # Procesar
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "biblioteca.zip")
            extract_path = os.path.join(temp_dir, "biodescodificacion_db")
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            
            # Cargar embeddings
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            vector_store = Chroma(persist_directory=extract_path, embedding_function=embeddings)
            
            # Conectar con IA
            llm = ChatGroq(
                groq_api_key=GROQ_API_KEY,
                model_name="meta-llama/llama-4-scout-17b-16e-instruct",
                temperature=0.3,
                max_tokens=3500
            )
            
            # Crear sistema RAG
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
    page_title="MINDGEEKCLINIC - Biodescodificación con Triangulación",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/271/271226.png", width=80)
    st.markdown("### 🏥 MINDGEEKCLINIC")
    st.markdown("**Sistema Profesional con Triangulación Diagnóstica**")
    st.markdown("---")
    
    st.markdown("#### 📊 Estadísticas")
    if "pacientes" in st.session_state:
        st.metric("Pacientes atendidos", len(st.session_state.pacientes))
    
    st.markdown("---")
    
    if st.button("🆕 Nuevo Diagnóstico", use_container_width=True, type="primary"):
        st.session_state.mostrar_diagnostico = False
        st.session_state.generar_guion = False
        st.session_state.generar_grabacion = False
        st.session_state.pdf_generado = None
        st.rerun()
    
    if st.button("🔄 Reiniciar Sistema", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()
    
    st.markdown("---")
    st.caption("🎯 Sistema con Triangulación de Eventos Emocionales")

# Título principal
st.title("🧠 MINDGEEKCLINIC")
st.markdown("### **Sistema de Diagnóstico por Biodescodificación con Triangulación Emocional**")
st.markdown("*Identificación precisa de relaciones evento-síntoma para protocolos personalizados*")
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
    
    # Mostrar datos del paciente con nueva información
    st.markdown(f"### 📄 **PACIENTE:** {paciente['iniciales']} • {paciente['edad']} años")
    
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
            st.write(f"**Factores desencadenantes:** {paciente['factores_desencadenantes'][:150]}...")
        
        st.markdown("#### 🎯 **Eventos Emocionales para Triangulación:**")
        st.info(paciente['eventos_emocionales'])
    
    # Generar diagnóstico con triangulación
    st.markdown("---")
    st.markdown("### 🔬 **DIAGNÓSTICO CON TRIANGULACIÓN EMOCIONAL**")
    
    if st.session_state.diagnostico_completo is None:
        with st.spinner("🔄 Analizando patrones evento-síntoma..."):
            diagnostico = generar_diagnostico_triangulacion(sistema, paciente)
            st.session_state.diagnostico_completo = diagnostico
    
    # Mostrar diagnóstico
    st.markdown(st.session_state.diagnostico_completo)
    
    # ==== SECCIÓN DE HIPNOSIS MEJORADA ====
    st.markdown("---")
    st.markdown("### 🎧 **PROTOCOLOS DE HIPNOSIS ESPECÍFICOS**")
    
    if not st.session_state.generar_guion and not st.session_state.generar_grabacion:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 👨‍⚕️ **Para aplicación por terapeuta:**")
            st.info("""
            **Basado en biblioteca de modelos de hipnosis:**
            - Técnicas específicas de inducción
            - Protocolos validados
            - Duración: 15-20 minutos
            - Frecuencia: 3 veces/semana
            """)
            
            if st.button("📝 Generar guión COMPLETO para terapeuta", use_container_width=True):
                st.session_state.generar_guion = True
                st.rerun()
        
        with col2:
            st.markdown("#### 🎵 **Para autohipnosis (grabación personal):**")
            st.info("""
            **Instrucciones específicas de la biblioteca:**
            - Técnicas de autoinducción
            - Sugerencias poshipnóticas
            - Grabación en dispositivo de audio
            - Escuchar 3 veces por semana
            """)
            
            if st.button("🎤 Generar guión para GRABACIÓN", use_container_width=True):
                st.session_state.generar_grabacion = True
                st.rerun()
    
    # Generar guiones específicos
    if st.session_state.generar_guion:
        st.markdown("---")
        st.markdown("### 👨‍⚕️ **GUIÓN COMPLETO PARA TERAPEUTA**")
        with st.spinner("Generando guión basado en biblioteca de modelos..."):
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
            
            # Instrucciones adicionales para grabación
            st.markdown("---")
            st.markdown("#### 📋 **INSTRUCCIONES PARA GRABACIÓN:**")
            st.success("""
            1. **Preparación:** Ambiente tranquilo, sin interrupciones
            2. **Equipo:** Usar micrófono de buena calidad o smartphone
            3. **Voz:** Hablar lentamente, con tono calmado
            4. **Pausas:** Dejar espacios para respiración
            5. **Guardar:** Nombrar archivo claramente (ej: "Autohipnosis_[fecha]")
            6. **Uso:** Escuchar con auriculares, posición cómoda
            """)
            
            if st.button("↩️ Volver a opciones", use_container_width=True):
                st.session_state.generar_grabacion = False
                st.rerun()
    
    # ===== BOTÓN DE GUARDAR COMO PDF =====
    st.markdown("---")
    st.markdown("### 💾 **GUARDAR DIAGNÓSTICO COMPLETO**")
    
    col_n1, col_n2, col_n3 = st.columns([2, 1, 1])
    
    with col_n1:
        if st.button("🆕 Realizar NUEVO diagnóstico", use_container_width=True, type="primary"):
            st.session_state.mostrar_diagnostico = False
            st.session_state.diagnostico_completo = None
            st.session_state.generar_guion = False
            st.session_state.generar_grabacion = False
            st.session_state.pdf_generado = None
            st.rerun()
    
    with col_n2:
        if st.button("📄 Generar y Descargar PDF", use_container_width=True, type="secondary"):
            with st.spinner("🔄 Generando PDF profesional..."):
                if st.session_state.paciente_actual and st.session_state.diagnostico_completo:
                    # Generar PDF
                    pdf_bytes = generar_pdf_diagnostico(
                        st.session_state.paciente_actual,
                        st.session_state.diagnostico_completo
                    )
                    
                    if pdf_bytes:
                        st.session_state.pdf_generado = pdf_bytes
                        st.success("✅ PDF generado correctamente")
                        
                        # Mostrar botón de descarga
                        nombre_archivo = f"Diagnostico_{paciente['iniciales']}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                        st.markdown("---")
                        st.markdown("#### 📥 **Descargar PDF**")
                        
                        # Crear botón de descarga
                        b64 = base64.b64encode(pdf_bytes).decode()
                        href = f'<a href="data:application/pdf;base64,{b64}" download="{nombre_archivo}" target="_blank">'
                        href += '<button style="background-color: #4CAF50; color: white; padding: 14px 28px; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; width: 100%; font-weight: bold;">📥 Descargar PDF ahora</button>'
                        href += '</a>'
                        
                        st.markdown(href, unsafe_allow_html=True)
                        
                        # Información del archivo
                        st.info(f"""
                        **Archivo:** {nombre_archivo}
                        **Tamaño:** {len(pdf_bytes) / 1024:.1f} KB
                        **Compatible:** Teléfono, Tablet, Computador
                        **Contenido:** Datos del paciente + Diagnóstico completo
                        """)
                    else:
                        st.error("❌ Error al generar el PDF")
                else:
                    st.warning("⚠️ No hay diagnóstico para generar PDF")
    
    with col_n3:
        if st.button("🖨️ Más opciones", use_container_width=True):
            with st.expander("📋 Opciones adicionales"):
                st.markdown("""
                **Opciones de exportación:**
                - **Imprimir directamente:** Usa Ctrl+P en la página
                - **Compartir por email:** Adjunta el PDF descargado
                - **Guardar en la nube:** Sube el PDF a Google Drive, Dropbox, etc.
                - **Archivar:** Guarda en carpeta de pacientes
                
                **Formato del PDF:**
                - Portada profesional
                - Datos completos del paciente
                - Diagnóstico estructurado
                - Información legal y de confidencialidad
                """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.8em;'>
    🧠 <b>MINDGEEKCLINIC v6.0</b> • Sistema con Triangulación Diagnóstica • 
    Incluye generación de PDF profesional para descarga • 
    Compatible con móvil y computador
    </div>
    """,
    unsafe_allow_html=True
)
