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
import re  # Importación añadida para limpiar HTML

# ================= CONFIGURACIÓN =================
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")
ZIP_URL = "https://github.com/alkhimiya/mindgeekclinicdeployment/raw/refs/heads/main/mindgeekclinic_db.zip"

# ================= SISTEMA DE CONOCIMIENTO ESPECIALIZADO (NUEVO MÓDULO) =================

CONOCIMIENTO_ESPECIALIZADO = {
    # ===== SISTEMA 1: OCULAR (EJEMPLO COMPLETO) =====
    "ojos": {
        "categoria": "sensorial",
        "palabras_clave": ["ojo", "ocular", "vista", "visión", "miopía", "astigmatismo", 
                          "conjuntivitis", "glaucoma", "retina", "catarata", "blefaritis",
                          "orzuelo", "perrilla", "queratitis", "irritación ocular", "sequedad ocular"],
        "prioridad": 1,
        "contenido": """## 🎯 BIODESCODIFICACIÓN ESPECIALIZADA - SISTEMA OCULAR

**REPRESENTACIÓN SIMBÓLICA:**
Los ojos representan mi capacidad de ver: pasado, presente y futuro.
Problemas oculares = Algo que no quiero ver en mi vida.

**ESPECIFICIDADES POR OJO:**
• **OJO IZQUIERDO:** Defensa, amenazas, movimiento, peligros externos
  - Conflictos relacionados con protección, enemigos, peligro inminente
  - "¿De qué o de quién necesito defenderme?"

• **OJO DERECHO:** Identidad, reconocimiento, relaciones cercanas
  - Conflictos con familia, amigos, reconocimiento personal/profesional
  - "¿Me siento reconocido? ¿Problemas con personas cercanas?"

**SÍNTOMAS ESPECÍFICOS Y SUS SIGNIFICADOS:**
- **IRRITACIÓN OCULAR:** "Algo de lo que veo me irrita. El mundo que veo a mi alrededor me irrita."
- **QUERATITIS:** "Estoy muy molesto, tengo ira y coraje por algo que vi."
- **SEQUEDAD OCULAR:** "Veo a todos con furia. Me niego rotundamente a ver con amor."
- **ORZUELO/PERRILLA:** "He visto algo sucio. Tengo problemas en mi matrimonio o con mi pareja."

**PREGUNTAS CLAVE PARA EL PACIENTE:**
1. ¿Qué situación actual prefiere no ver o enfrentar?
2. Si es ojo derecho: ¿Problemas recientes de reconocimiento o con familiares/amigos?
3. Si es ojo izquierdo: ¿Amenazas o situaciones de defensa recientes?
4. ¿Eventos visuales que generaron ira, coraje o rechazo?

**PROTOCOLO SUGERIDO:**
1. Identificar el evento detonante visual/emocional
2. Trabajar el resentir específico según el síntoma
3. Reestructurar la percepción del evento
4. Ejercicios de "nueva mirada" hacia la situación"""
    },
    
    # ===== SISTEMA 2: DERMATOLÓGICO (EJEMPLO BÁSICO) =====
    "piel": {
        "categoria": "dermatologico",
        "palabras_clave": ["piel", "dermatitis", "eczema", "acné", "urticaria", "psoriasis", 
                          "erupción", "prurito", "picazón", "roncha", "sarpullido"],
        "prioridad": 1,
        "contenido": """## 🎯 BIODESCODIFICACIÓN ESPECIALIZADA - PIEL

**REPRESENTACIÓN SIMBÓLICA:**
La piel representa el contacto, los límites, la protección.
Problemas cutáneos = Conflictos de separación, contacto no deseado, límites violados.

**SÍNTOMAS ESPECÍFICOS:**
- **DERMATITIS:** Separación conflictiva, contacto doloroso o no deseado
- **ACNÉ:** No aceptación de sí mismo, conflictos de identidad (especialmente en adolescencia)
- **PSORIASIS:** Miedo a ser herido, necesidad de protección extrema
- **URTICARIA:** "Algo o alguien me irrita profundamente"

**PREGUNTAS CLAVE:**
1. ¿Situaciones donde sus límites personales fueron violados?
2. ¿Contactos físicos o emocionales no deseados recientes?
3. ¿Conflictos de separación (física o emocional)?
4. ¿Se siente "sin protección" en alguna área de su vida?"""
    },
    
    # ===== SISTEMA 3: DIGESTIVO (EJEMPLO BÁSICO) =====
    "sistema_digestivo": {
        "categoria": "digestivo",
        "palabras_clave": ["estómago", "gástrico", "digestión", "úlcera", "gastritis", "acidez",
                          "reflujo", "colon", "intestino", "diarrea", "estreñimiento", "náusea"],
        "prioridad": 1,
        "contenido": """## 🎯 BIODESCODIFICACIÓN ESPECIALIZADA - SISTEMA DIGESTIVO

**REPRESENTACIÓN SIMBÓLICA:**
Capacidad de "digerir" situaciones, asimilar experiencias, procesar emociones.

**ESPECIFICIDADES POR ÓRGANO:**
- **ESTOMÁGO:** "No puedo digerir esta situación"
- **HÍGADO:** Ira reprimida, frustración acumulada
- **COLON:** Miedo a soltar, apego a lo viejo
- **INTESTINO DELGADO:** Incapacidad de extraer el "nutriente emocional" de las experiencias

**PREGUNTAS CLAVE:**
1. ¿Qué situación actual no puede "digerir" o aceptar?
2. ¿Hay ira o frustración que no ha podido expresar?
3. ¿Miedo a soltar algo o a alguien?
4. ¿Qué "no nutre" en su vida actualmente?"""
    },
    
    # ===== SISTEMA 4: RESPIRATORIO =====
    "sistema_respiratorio": {
        "categoria": "respiratorio",
        "palabras_clave": ["pulmón", "respiración", "asma", "bronquitis", "tos", "congestión",
                          "nariz", "sinusitis", "alergia", "resfriado", "gripe", "falta de aire"],
        "prioridad": 1,
        "contenido": """## 🎯 BIODESCODIFICACIÓN ESPECIALIZADA - SISTEMA RESPIRATORIO

**REPRESENTACIÓN SIMBÓLICA:**
Vida, comunicación, libertad, espacio vital.
Problemas respiratorios = Conflictos con el territorio, miedo a la muerte, falta de libertad.

**ESPECIFICIDADES POR SÍNTOMA:**
- **ASMA:** "Me siento ahogado en mi territorio (hogar, trabajo, familia)"
- **BRONQUITIS:** Conflictos de territorio con peleas o gritos
- **RINITIS/ALERGIA:** "El aire que respiro (ambiente) me molesta"
- **SINUSITIS:** "Alguien cercano me irrita profundamente"

**PREGUNTAS CLAVE:**
1. ¿Se siente ahogado o limitado en algún aspecto de su vida?
2. ¿Conflictos territoriales (hogar, trabajo, familia)?
3. ¿Alguien o algo en su ambiente le "quita el aire"?
4. ¿Miedo a morir o a perder algo vital?"""
    },
    
    # ===== SISTEMA 5: MUSCULAR =====
    "sistema_muscular": {
        "categoria": "musculoesqueletico",
        "palabras_clave": ["músculo", "dolor muscular", "contractura", "espasmo", "calambre",
                          "tendón", "tendinitis", "fibromialgia", "rigidez", "tensión muscular"],
        "prioridad": 1,
        "contenido": """## 🎯 BIODESCODIFICACIÓN ESPECIALIZADA - SISTEMA MUSCULAR

**REPRESENTACIÓN SIMBÓLICA:**
Acción, movimiento, capacidad de actuar.
Problemas musculares = Conflictos de desvalorización en la acción, impotencia para actuar.

**ESPECIFICIDADES POR LOCALIZACIÓN:**
- **CUELLO/HOMBROS:** "Llevo una carga demasiado pesada"
- **ESPALDA BAJA:** Falta de apoyo, sobrecarga de responsabilidades
- **PIERNAS:** "No puedo avanzar en la vida", miedo al futuro
- **BRAZOS:** Conflictos en lo que hago o en lo que deseo abrazar/rechazar

**PREGUNTAS CLAVE:**
1. ¿En qué área de su vida se siente impotente para actuar?
2. ¿Qué carga emocional está "llevando a cuestas"?
3. ¿Se siente desvalorizado en sus capacidades?
4. ¿Hay algo que quiere hacer pero no puede?"""
    }
}

def buscar_conocimiento_especializado(dolencia):
    """
    Busca conocimiento especializado relevante para la dolencia.
    Retorna el conocimiento encontrado o string vacío si no hay coincidencia.
    """
    if not dolencia or not isinstance(dolencia, str):
        return ""
    
    dolencia_lower = dolencia.lower()
    conocimientos_encontrados = []
    
    for sistema, info in CONOCIMIENTO_ESPECIALIZADO.items():
        # Verificar si alguna palabra clave aparece en la dolencia
        for palabra_clave in info["palabras_clave"]:
            if palabra_clave in dolencia_lower:
                conocimientos_encontrados.append({
                    "sistema": sistema,
                    "contenido": info["contenido"],
                    "prioridad": info["prioridad"]
                })
                break
    
    conocimientos_encontrados.sort(key=lambda x: x["prioridad"])
    
    if conocimientos_encontrados:
        resultado = "="*60 + "\n"
        resultado += "🎯 **CONOCIMIENTO ESPECIALIZADO APLICABLE**\n"
        resultado += "="*60 + "\n\n"
        
        for i, conocimiento in enumerate(conocimientos_encontrados, 1):
            resultado += conocimiento["contenido"]
            if i < len(conocimientos_encontrados):
                resultado += "\n\n" + "-"*40 + "\n\n"
        
        return resultado
    
    return ""

# ================= FUNCIÓN PARA GENERAR PDF =================
def generar_pdf_diagnostico(datos_paciente, diagnostico):
    """
    Genera un PDF profesional con el diagnóstico completo.
    Retorna el PDF como bytes para descarga.
    """
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
        
        # ===== SECCIÓN 1: DATOS DEL PACIENTE =====
        story.append(Paragraph("INFORMACIÓN DEL PACIENTE", estilo_titulo))
        story.append(Spacer(1, 0.25*inch))
        
        datos_basicos = [
            ["<b>Estado Civil:</b>", datos_paciente['estado_civil']],
            ["<b>Situación Laboral:</b>", datos_paciente['situacion_laboral']],
            ["<b>Tensión Arterial:</b>", datos_paciente['tension']],
            ["<b>Tiempo Padecimiento:</b>", datos_paciente['tiempo_padecimiento']],
            ["<b>Frecuencia:</b>", datos_paciente['frecuencia']],
            ["<b>Intensidad:</b>", f"{datos_paciente['intensidad']}/10"]
        ]
        
        if datos_paciente.get('diagnostico_medico') and datos_paciente['diagnostico_medico'].strip():
            datos_basicos.append(["<b>Diagnóstico Médico:</b>", datos_paciente['diagnostico_medico']])
        
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
        
        story.append(Paragraph("DOLENCIA PRINCIPAL", estilo_subtitulo))
        story.append(Paragraph(datos_paciente['dolencia'], estilo_cuerpo))
        story.append(Spacer(1, 0.2*inch))
        
        if datos_paciente.get('factores_desencadenantes'):
            story.append(Paragraph("FACTORES DESENCADENANTES", estilo_subtitulo))
            story.append(Paragraph(datos_paciente['factores_desencadenantes'], estilo_cuerpo))
            story.append(Spacer(1, 0.2*inch))
        
        story.append(Paragraph("EVENTOS EMOCIONALES ASOCIADOS", estilo_subtitulo))
        story.append(Paragraph(datos_paciente['eventos_emocionales'], estilo_cuerpo))
        story.append(Spacer(1, 0.2*inch))
        
        story.append(Paragraph("ENTORNO SOCIAL", estilo_subtitulo))
        story.append(Paragraph(datos_paciente['entorno_social'], estilo_cuerpo))
        
        story.append(PageBreak())
        
        # ===== SECCIÓN 2: DIAGNÓSTICO =====
        story.append(Paragraph("DIAGNÓSTICO DE BIODESCODIFICACIÓN", estilo_titulo))
        story.append(Spacer(1, 0.25*inch))
        
        def limpiar_texto_para_pdf(texto):
            if not texto:
                return ""
            
            texto = texto.replace(' ', ' ').replace('\xa0', ' ')
            texto = texto.replace('**', '').replace('__', '')
            texto = re.sub(r'<[^>]*>', '', texto)
            texto = texto.replace('&nbsp;', ' ')
            texto = texto.replace('&amp;', '&')
            texto = texto.replace('&lt;', '<')
            texto = texto.replace('&gt;', '>')
            texto = texto.replace('&quot;', '"')
            texto = re.sub(r'\s+', ' ', texto)
            
            lineas = texto.split('\n')
            lineas_limpias = []
            
            for linea in lineas:
                linea = linea.strip()
                if linea:
                    if linea and len(linea) > 1:
                        linea = linea[0].upper() + linea[1:]
                    lineas_limpias.append(linea)
            
            return '<br/>'.join(lineas_limpias)
        
        diagnostico_limpio = limpiar_texto_para_pdf(diagnostico)
        
        if diagnostico_limpio:
            secciones = diagnostico_limpio.split('<br/>')
            
            for seccion in secciones:
                seccion = seccion.strip()
                if not seccion:
                    continue
                
                if (seccion.startswith('### ') or seccion.startswith('## ') or 
                    seccion.startswith('# ') or seccion.endswith(':')):
                    
                    if seccion.startswith('###'):
                        estilo = ParagraphStyle(
                            'SubSubHeader',
                            parent=styles['Normal'],
                            fontSize=11,
                            textColor=colors.HexColor('#1E3A8A'),
                            spaceBefore=10,
                            spaceAfter=4
                        )
                        seccion = seccion.replace('###', '').strip()
                        story.append(Paragraph(f"<b>{seccion}</b>", estilo))
                    elif seccion.startswith('##'):
                        estilo = ParagraphStyle(
                            'SubHeader',
                            parent=styles['Normal'],
                            fontSize=12,
                            textColor=colors.HexColor('#1E3A8A'),
                            spaceBefore=12,
                            spaceAfter=6
                        )
                        seccion = seccion.replace('##', '').strip()
                        story.append(Paragraph(f"<b>{seccion}</b>", estilo))
                    elif seccion.startswith('#'):
                        estilo = ParagraphStyle(
                            'MainHeader',
                            parent=styles['Normal'],
                            fontSize=14,
                            textColor=colors.HexColor('#1E3A8A'),
                            spaceBefore=14,
                            spaceAfter=8
                        )
                        seccion = seccion.replace('#', '').strip()
                        story.append(Paragraph(f"<b>{seccion}</b>", estilo))
                    else:
                        story.append(Paragraph(f"<b>{seccion}</b>", estilo_subtitulo))
                else:
                    story.append(Paragraph(seccion, estilo_diagnostico))
        
        story.append(Spacer(1, 0.3*inch))
        
        # ===== SECCIÓN 3: INFORMACIÓN LEGAL =====
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
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
        
    except Exception as e:
        st.error(f"Error al generar PDF: {str(e)}")
        return None

# ================= FUNCIONES DE BASE DE DATOS =================
def descargar_y_extraer_db():
    """Descarga y extrae la base de datos vectorial desde GitHub"""
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, "mindgeekclinic_db.zip")
            
            # Descargar el zip
            response = requests.get(ZIP_URL, stream=True)
            if response.status_code == 200:
                with open(zip_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Extraer el zip
                extract_path = os.path.join(tmpdir, "db")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)
                
                return extract_path
            else:
                st.error(f"Error al descargar la base de datos: {response.status_code}")
                return None
    except Exception as e:
        st.error(f"Error en descarga/extracción: {str(e)}")
        return None

def cargar_base_datos():
    """Carga la base de datos vectorial"""
    try:
        db_path = descargar_y_extraer_db()
        if db_path:
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            vectorstore = Chroma(persist_directory=db_path, embedding_function=embeddings)
            return vectorstore
        return None
    except Exception as e:
        st.error(f"Error al cargar base de datos: {str(e)}")
        return None

# ================= CONFIGURACIÓN STREAMLIT =================
st.set_page_config(
    page_title="MINDGEEKCLINIC - Biodescodificación Profesional",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= SIDEBAR - FORMULARIO DEL PACIENTE =================
with st.sidebar:
    st.image("https://raw.githubusercontent.com/alkhimiya/mindgeekclinicdeployment/refs/heads/main/logo%20(1).png", width=200)
    st.title("🧠 MINDGEEKCLINIC")
    st.markdown("**Sistema Profesional de Biodescodificación**")
    
    st.divider()
    
    st.subheader("📋 Datos del Paciente")
    
    # Campos del formulario - SOLO CAMBIÉ EL ORDEN: DOLENCIA antes de TIEMPO DE PADECIMIENTO
    iniciales = st.text_input("Iniciales del paciente (ej: A.B.):", max_chars=10)
    edad = st.number_input("Edad:", min_value=1, max_value=120, value=30)
    estado_civil = st.selectbox("Estado civil:", ["Soltero/a", "Casado/a", "Divorciado/a", "Viudo/a", "Unión libre", "Otro"])
    situacion_laboral = st.selectbox("Situación laboral:", ["Empleado", "Desempleado", "Independiente", "Estudiante", "Jubilado", "Otro"])
    tension = st.selectbox("Tensión arterial:", ["Normal", "Hipotensión", "Hipertensión", "No sabe"])
    
    # CAMBIO ÚNICO: DOLENCIA movida aquí (antes estaba después de "Tiempo de padecimiento")
    dolencia = st.text_area("Dolencia o síntoma principal:", 
                           placeholder="Describa su dolencia principal (ej: dolor de cabeza recurrente, ansiedad, problemas digestivos...)", 
                           height=80)
    
    # TIEMPO DE PADECIMIENTO ahora viene DESPUÉS de la dolencia
    tiempo_padecimiento = st.text_input("Tiempo de padecimiento (ej: 3 meses, 2 años, desde la infancia):")
    frecuencia = st.selectbox("Frecuencia:", ["Constante", "Diaria", "Semanal", "Mensual", "Ocasional", "Variable"])
    intensidad = st.slider("Intensidad (1-10):", min_value=1, max_value=10, value=5)
    
    st.divider()
    
    st.subheader("🩺 Información Médica Adicional")
    diagnostico_medico = st.text_area("Diagnóstico médico previo (si existe):", 
                                     placeholder="Si tiene diagnóstico médico formal, indíquelo aquí...", 
                                     height=60)
    
    st.divider()
    
    st.subheader("🧩 Factores Contextuales")
    factores_desencadenantes = st.text_area("Factores desencadenantes o agravantes:", 
                                           placeholder="¿Qué situaciones empeoran el síntoma? (estrés, ciertos alimentos, conflictos familiares...)", 
                                           height=80)
    eventos_emocionales = st.text_area("Eventos emocionales recientes:", 
                                      placeholder="Eventos significativos (pérdidas, cambios, conflictos) previos o durante el padecimiento...", 
                                      height=80)
    entorno_social = st.text_area("Entorno social y familiar:", 
                                 placeholder="Describa brevemente su entorno social, familiar y relaciones importantes...", 
                                 height=80)
    
    st.divider()
    
    # Botón para generar diagnóstico
    generar_diagnostico = st.button("🔍 GENERAR DIAGNÓSTICO", type="primary", use_container_width=True)
    
    st.caption("v6.0 - Sistema de Triangulación Diagnóstica")

# ================= ÁREA PRINCIPAL =================
st.title("🧠 MINDGEEKCLINIC - Sistema de Biodescodificación")
st.markdown("### Plataforma Profesional de Análisis Psico-Emocional y Biodescodificación")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    **¿Qué es la biodescodificación?**
    
    La biodescodificación es un enfoque que estudia la correlación entre las emociones inconscientes 
    y las manifestaciones físicas (síntomas, enfermedades). Este sistema utiliza inteligencia artificial 
    especializada para analizar patrones emocionales asociados a dolencias específicas.
    """)

with col2:
    st.info("""
    **⚠️ Aviso Importante:**
    Este sistema es una herramienta de apoyo para profesionales. 
    No sustituye diagnóstico médico ni tratamiento profesional.
    """)

st.divider()

# ================= PROCESAMIENTO DEL DIAGNÓSTICO =================
if generar_diagnostico:
    # Validar campos obligatorios
    if not iniciales or not dolencia:
        st.error("❌ Por favor, complete al menos las iniciales y la dolencia principal.")
        st.stop()
    
    # Mostrar indicador de carga
    with st.spinner("🔍 Analizando caso y generando diagnóstico..."):
        try:
            # Recopilar datos del paciente
            datos_paciente = {
                'iniciales': iniciales,
                'edad': edad,
                'estado_civil': estado_civil,
                'situacion_laboral': situacion_laboral,
                'tension': tension,
                'dolencia': dolencia,
                'tiempo_padecimiento': tiempo_padecimiento,
                'frecuencia': frecuencia,
                'intensidad': intensidad,
                'diagnostico_medico': diagnostico_medico,
                'factores_desencadenantes': factores_desencadenantes,
                'eventos_emocionales': eventos_emocionales,
                'entorno_social': entorno_social
            }
            
            # Buscar conocimiento especializado PRIMERO
            conocimiento_especializado = buscar_conocimiento_especializado(dolencia)
            
            # Cargar base de datos
            vectorstore = cargar_base_datos()
            
            if not vectorstore:
                st.error("❌ No se pudo cargar la base de datos de conocimiento.")
                st.stop()
            
            # Configurar LLM
            llm = ChatGroq(
                temperature=0.7,
                model_name="mixtral-8x7b-32768",
                groq_api_key=GROQ_API_KEY
            )
            
            # Configurar sistema de recuperación
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=vectorstore.as_retriever(search_kwargs={"k": 4}),
                return_source_documents=True
            )
            
            # Construir contexto del caso
            contexto_caso = f"""
            DATOS DEL PACIENTE:
            - Iniciales: {iniciales}
            - Edad: {edad} años
            - Estado civil: {estado_civil}
            - Situación laboral: {situacion_laboral}
            - Tensión arterial: {tension}
            
            DOLENCIA PRINCIPAL:
            {dolencia}
            
            CARACTERÍSTICAS DEL SÍNTOMA:
            - Tiempo de padecimiento: {tiempo_padecimiento}
            - Frecuencia: {frecuencia}
            - Intensidad: {intensidad}/10
            
            CONTEXTO ADICIONAL:
            - Diagnóstico médico previo: {diagnostico_medico if diagnostico_medico else 'No especificado'}
            - Factores desencadenantes: {factores_desencadenantes if factores_desencadenantes else 'No especificados'}
            - Eventos emocionales recientes: {eventos_emocionales if eventos_emocionales else 'No especificados'}
            - Entorno social/familiar: {entorno_social if entorno_social else 'No especificado'}
            """
            
            # Prompt optimizado para biodescodificación
            prompt = f"""
            Eres un especialista en biodescodificación con 20 años de experiencia. Analiza el siguiente caso clínico y proporciona un diagnóstico de biodescodificación profesional.
            
            {contexto_caso}
            
            {conocimiento_especializado if conocimiento_especializado else ""}
            
            INSTRUCCIONES ESPECÍFICAS:
            1. **ANÁLISIS DE BIODESCODIFICACIÓN**:
               - Identifica el conflicto emocional probable asociado a la dolencia
               - Relaciona síntomas específicos con posibles emociones reprimidas
               - Considera simbolismo corporal según la localización del síntoma
            
            2. **CONTEXTO VITAL**:
               - Analiza cómo la edad, situación laboral y estado civil podrían influir
               - Evalúa eventos emocionales recientes como posibles desencadenantes
               - Considera el entorno social como factor de estrés o apoyo
            
            3. **RECOMENDACIONES ESPECÍFICAS**:
               - Sugiere preguntas terapéuticas para profundizar en el conflicto
               - Propone ejercicios o reflexiones específicas para el paciente
               - Indica posibles áreas a trabajar en terapia
            
            4. **FORMATO DE RESPUESTA**:
               - Usa títulos claros con ## y ###
               - Incluye viñetas para listas
               - Sé compasivo pero profesional
               - Mantén un tono científico pero accesible
            
            IMPORTANTE: Base tu análisis en principios científicos de biodescodificación, psiconeuroinmunología y medicina mente-cuerpo.
            """
            
            # Obtener respuesta del sistema
            respuesta = qa_chain({"query": prompt})
            diagnostico = respuesta['result']
            
            # Mostrar resultados
            st.success("✅ Diagnóstico generado exitosamente!")
            
            # Mostrar diagnóstico
            with st.expander("📄 **DIAGNÓSTICO COMPLETO DE BIODESCODIFICACIÓN**", expanded=True):
                # Añadir conocimiento especializado al inicio si existe
                if conocimiento_especializado:
                    st.markdown("### 🎯 CONOCIMIENTO ESPECIALIZADO APLICABLE")
                    st.markdown(conocimiento_especializado)
                    st.divider()
                
                st.markdown(diagnostico)
            
            # Generar y ofrecer PDF
            st.divider()
            st.subheader("📥 Descargar Reporte Profesional")
            
            pdf_bytes = generar_pdf_diagnostico(datos_paciente, diagnostico)
            
            if pdf_bytes:
                # Codificar PDF para descarga
                b64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
                pdf_filename = f"Diagnostico_MG_{iniciales}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                
                # Botón de descarga
                st.download_button(
                    label="📄 DESCARGAR PDF PROFESIONAL",
                    data=pdf_bytes,
                    file_name=pdf_filename,
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )
                
                st.caption("El PDF incluye: Datos del paciente, diagnóstico completo, recomendaciones y aviso legal.")
            
            # Mostrar resumen de datos
            with st.expander("📊 Resumen de Datos del Paciente"):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("Edad", f"{edad} años")
                    st.metric("Estado Civil", estado_civil)
                    st.metric("Intensidad", f"{intensidad}/10")
                
                with col_b:
                    st.metric("Situación Laboral", situacion_laboral)
                    st.metric("Frecuencia", frecuencia)
                    st.metric("Tensión", tension)
            
        except Exception as e:
            st.error(f"❌ Error en el procesamiento: {str(e)}")
            st.info("Por favor, intente nuevamente o contacte con soporte.")

# ================= INFORMACIÓN ADICIONAL =================
else:
    st.info("""
    👈 **Complete el formulario en la barra lateral y haga clic en 'GENERAR DIAGNÓSTICO' para comenzar.**
    
    El sistema analizará:
    1. La dolencia desde la perspectiva de la biodescodificación
    2. Factores emocionales y psicosociales
    3. Patrones recurrentes y conflictos inconscientes
    4. Recomendaciones específicas para el trabajo terapéutico
    """)
    
    # Mostrar sistemas especializados disponibles
    with st.expander("📚 Sistemas de Biodescodificación Especializados Disponibles"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**👁️ Sistema Ocular**")
            st.caption("Problemas visuales, irritación, sequedad")
            
            st.markdown("**🫁 Sistema Respiratorio**")
            st.caption("Asma, alergias, problemas respiratorios")
        
        with col2:
            st.markdown("**🩸 Sistema Dermatológico**")
            st.caption("Piel, dermatitis, acné, psoriasis")
            
            st.markdown("**💪 Sistema Muscular**")
            st.caption("Dolores, contracturas, tensiones")
        
        with col3:
            st.markdown("**🍽️ Sistema Digestivo**")
            st.caption("Problemas gástricos, intestinales")
            
            st.markdown("**🧠 Sistema Neurológico**")
            st.caption("Cefaleas, migrañas, neuralgias")
    
    st.divider()
    st.caption("Sistema MINDGEEKCLINIC v6.0 - © 2024 Todos los derechos reservados")
