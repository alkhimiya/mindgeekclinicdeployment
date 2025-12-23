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
import re

# ================= CONFIGURACIÓN SEGURA =================
# CORRECCIÓN: Solo leer de secrets, NO poner la clave en el código
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")  # ← SOLO esta línea
ZIP_URL = "https://github.com/alkhimiya/mindgeekclinicdeployment/raw/refs/heads/main/mindgeekclinic_db.zip"

# ================= CONFIGURACIÓN CONOCIMIENTO ESPECIALIZADO =================
CONOCIMIENTO_ESPECIALIZADO_URL = "https://docs.google.com/document/d/1BZa1rid24RpRWU2nOOxOQYAaynWD5I7lg9FJrbvUMZg/edit?usp=drivesdk"
CONOCIMIENTO_DOWNLOAD_URL = "https://docs.google.com/document/d/1BZa1rid24RpRWU2nOOxOQYAaynWD5I7lg9FJrbvUMZg/export?format=txt"

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
    datos["id"] = f"{datos['iniciales']}_{len(st.session_state.pacientes)+1:03d}"
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

# ================= FUNCIÓN PARA GENERAR PDF =================
def generar_pdf_diagnostico(datos_paciente, diagnostico):
    """Genera un PDF profesional con el diagnóstico completo."""
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
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
        
        # ... (Mantener todos los estilos y lógica PDF existentes) ...
        
        # Contenido del PDF
        story = []
        
        # ===== PORTADA =====
        story.append(Spacer(1, 2*inch))
        story.append(Paragraph("🧠", ParagraphStyle('Logo', parent=styles['Heading1'], fontSize=48, alignment=TA_CENTER)))
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph("MINDGEEKCLINIC", ParagraphStyle('MainTitle', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#1E3A8A'), alignment=TA_CENTER)))
        story.append(Paragraph("Sistema Profesional de Biodescodificación", ParagraphStyle('Subtitle', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#6B7280'), alignment=TA_CENTER)))
        story.append(Spacer(1, inch))
        
        info_paciente = [
            ["<b>PACIENTE:</b>", datos_paciente['iniciales']],
            ["<b>EDAD:</b>", f"{datos_paciente['edad']} años"],
            ["<b>FECHA:</b>", datetime.now().strftime("%d/%m/%Y %H:%M")],
            ["<b>ID:</b>", f"MG-{datos_paciente['iniciales']}-{datetime.now().strftime('%Y%m%d')}"]
        ]
        
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
        
        # ... (Mantener resto de lógica PDF) ...
        
        # ===== GENERAR PDF =====
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
        
    except Exception as e:
        st.error(f"Error al generar PDF: {str(e)}")
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
    
    3. **ESTRUCTURA DEL DIAGNÓSTICO:**
       ### 🔍 DIAGNÓSTICO POR TRIANGULACIÓN
       [Explicar relación eventos-síntomas]
       
       ### 🎯 CONFLICTO EMOCIONAL IDENTIFICADO
       [Conflicto específico + significado biológico]
       
       ### 📊 INTEGRACIÓN DE CONOCIMIENTO ESPECIALIZADO
       [Cómo se aplica el conocimiento especializado a este caso]
       
       ### 💡 PROTOCOLO DE 3 SESIONES TERAPÉUTICAS
       Sesión 1: [Enfoque específico]
       Sesión 2: [Trabajo emocional]
       Sesión 3: [Integración y estrategias]
       
       ### 🎧 PROTOCOLO DE HIPNOSIS/AUTOHIPNOSIS
       [Instrucciones basadas en biblioteca de modelos]
    
    4. **REQUISITOS ESTRICTOS:**
       - DEBE usar la biblioteca de biodescodificación disponible
       - DEBE integrar el conocimiento especializado cuando sea relevante
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
                max_tokens=3500
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
    page_title="MINDGEEKCLINIC - Biodescodificación con Triangulación",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/271/271226.png", width=80)
    st.markdown("### 🏥 MINDGEEKCLINIC")
    st.markdown("**Sistema con Conocimiento Especializado**")
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
    st.caption("🎯 Sistema con Triangulación y Conocimiento Especializado")

# Título principal
st.title("🧠 MINDGEEKCLINIC")
st.markdown("### **Sistema de Diagnóstico con Conocimiento Especializado Integrado**")
st.markdown("*Diagnósticos enriquecidos con análisis único de suicidios, lupus, adicciones, autismo y más*")
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
    st.markdown("### 🔬 **DIAGNÓSTICO CON TRIANGULACIÓN Y CONOCIMIENTO ESPECIALIZADO**")
    
    if st.session_state.diagnostico_completo is None:
        with st.spinner("🔄 Analizando con conocimiento especializado..."):
            diagnostico = generar_diagnostico_triangulacion(sistema, paciente)
            st.session_state.diagnostico_completo = diagnostico
    
    # Mostrar diagnóstico
    st.markdown(st.session_state.diagnostico_completo)
    
    # ==== SECCIÓN DE HIPNOSIS ====
    st.markdown("---")
    st.markdown("### 🎧 **PROTOCOLOS DE HIPNOSIS ESPECÍFICOS**")
    
    if not st.session_state.generar_guion and not st.session_state.generar_grabacion:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 👨‍⚕️ **Para aplicación por terapeuta:**")
            st.info("Basado en biblioteca de modelos de hipnosis")
            
            if st.button("📝 Generar guión COMPLETO para terapeuta", use_container_width=True):
                st.session_state.generar_guion = True
                st.rerun()
        
        with col2:
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
                    pdf_bytes = generar_pdf_diagnostico(
                        st.session_state.paciente_actual,
                        st.session_state.diagnostico_completo
                    )
                    
                    if pdf_bytes:
                        st.session_state.pdf_generado = pdf_bytes
                        st.success("✅ PDF generado correctamente")
                        
                        nombre_archivo = f"Diagnostico_{paciente['iniciales']}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                        
                        b64 = base64.b64encode(pdf_bytes).decode()
                        href = f'<a href="data:application/pdf;base64,{b64}" download="{nombre_archivo}" target="_blank">'
                        href += '<button style="background-color: #4CAF50; color: white; padding: 14px 28px; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; width: 100%; font-weight: bold;">📥 Descargar PDF ahora</button>'
                        href += '</a>'
                        
                        st.markdown(href, unsafe_allow_html=True)
                    else:
                        st.error("❌ Error al generar el PDF")
                else:
                    st.warning("⚠️ No hay diagnóstico para generar PDF")
    
    with col_n3:
        if st.button("🖨️ Más opciones", use_container_width=True):
            with st.expander("📋 Opciones adicionales"):
                st.markdown("""
                **Opciones de exportación:**
                - **Imprimir directamente:** Usa Ctrl+P
                - **Compartir por email:** Adjunta el PDF
                - **Guardar en la nube:** Google Drive, Dropbox
                - **Archivar:** Guarda en carpeta de pacientes
                """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.8em;'>
    🧠 <b>MINDGEEKCLINIC v7.0</b> • Sistema con Conocimiento Especializado • 
    Triangulación Diagnóstica • Compatible con móvil y computador
    </div>
    """,
    unsafe_allow_html=True
)
