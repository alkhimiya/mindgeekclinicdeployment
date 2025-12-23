# app.py - MINDGEEKCLINIC v6.0 con Base de Conocimientos Expandida
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

# ================ IMPORTACIONES PARA PDF ================
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

# ================ IMPORTACIONES PARA CARGA DE DOCUMENTOS ================
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredWordDocumentLoader,
    CSVLoader
)
import io

# ================= CONFIGURACIÓN =================
# API Keys deben estar SOLO en secrets.toml
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")
ZIP_URL = "https://github.com/alkhimiya/mindgeekclinicdeployment/raw/refs/heads/main/mindgeekclinic_db.zip"
GOOGLE_DRIVE_URL = "https://drive.google.com/uc?export=download&id=1uePzkVSS8yHnTRwJYqoP0wL0rOGJ4TS9"

# ================= SISTEMA DE CONOCIMIENTO ESPECIALIZADO =================
CONOCIMIENTO_ESPECIALIZADO = {
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
- **ASMA:** "Me siente ahogado en mi territorio (hogar, trabajo, familia)"
- **BRONQUITIS:** Conflictos de territorio con peleas o gritos
- **RINITIS/ALERGIA:** "El aire que respiro (ambiente) me molesta"
- **SINUSITIS:** "Alguien cercano me irrita profundamente"

**PREGUNTAS CLAVE:**
1. ¿Se siente ahogado o limitado en algún aspecto de su vida?
2. ¿Conflictos territoriales (hogar, trabajo, familia)?
3. ¿Alguien o algo en su ambiente le "quita el aire"?
4. ¿Miedo a morir o a perder algo vital?"""
    },
    
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

# ================= FUNCIONES PARA CARGA DE DOCUMENTOS DE DRIVE =================
def cargar_documentos_drive(url_drive: str) -> list:
    """Carga documentos desde Google Drive y los procesa."""
    try:
        st.info("📥 Conectando con Google Drive para cargar conocimiento especializado...")
        response = requests.get(url_drive, timeout=30)
        
        if response.status_code != 200:
            st.warning(f"⚠️ No se pudo conectar con Google Drive (código {response.status_code})")
            return []
        
        # Determinar tipo de contenido
        content_type = response.headers.get('content-type', '').lower()
        
        # Preparar archivo temporal
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(response.content)
            tmp_path = tmp_file.name
        
        documentos = []
        
        # Intentar cargar como PDF (formato más común)
        try:
            loader = PyPDFLoader(tmp_path)
            docs = loader.load()
            documentos.extend(docs)
            st.success(f"✅ PDF cargado: {len(docs)} páginas procesadas")
        except Exception as e:
            st.warning(f"ℹ️ No es un PDF válido: {str(e)}")
        
        # Si no es PDF, intentar como texto
        if not documentos:
            try:
                with open(tmp_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                if len(content) > 100:  # Contenido significativo
                    doc = Document(
                        page_content=content,
                        metadata={"source": "Google Drive", "type": "conocimiento_especializado"}
                    )
                    documentos.append(doc)
                    st.success(f"✅ Texto cargado: {len(content)} caracteres")
            except:
                st.warning("ℹ️ No se pudo procesar como texto")
        
        # Limpiar archivo temporal
        os.unlink(tmp_path)
        
        if documentos:
            # Dividir en fragmentos manejables
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=800,
                chunk_overlap=150,
                length_function=len,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            
            documentos_divididos = text_splitter.split_documents(documentos)
            
            # Añadir metadatos consistentes
            for i, doc in enumerate(documentos_divididos):
                doc.metadata.update({
                    "source": "Google Drive - Conocimiento Avanzado",
                    "tipo": "conocimiento_especializado",
                    "id": f"drive_{i:04d}",
                    "fecha_carga": datetime.now().strftime("%Y-%m-%d")
                })
            
            st.success(f"📚 Base de conocimientos expandida: {len(documentos_divididos)} fragmentos especializados")
            return documentos_divididos
        
        return []
        
    except Exception as e:
        st.error(f"❌ Error al cargar desde Drive: {str(e)}")
        return []

def enriquecer_base_conocimientos(vector_store, documentos_drive: list):
    """Añade documentos de Drive a la base vectorial existente."""
    if not documentos_drive:
        return False
    
    try:
        # Verificar si ya existen documentos similares
        existing_ids = vector_store.get()['ids'] if hasattr(vector_store, 'get') else []
        
        # Generar IDs únicos
        start_id = len(existing_ids) if existing_ids else 0
        nuevos_ids = [f"drive_{start_id + i:04d}" for i in range(len(documentos_drive))]
        
        # Añadir a la base
        vector_store.add_documents(documents=documentos_drive, ids=nuevos_ids)
        
        st.success(f"🎯 Conocimiento de Drive integrado: {len(documentos_drive)} fragmentos")
        return True
        
    except Exception as e:
        st.error(f"❌ Error al integrar conocimiento: {str(e)}")
        return False

# ================= FUNCIONES EXISTENTES (MODIFICADAS) =================
def buscar_conocimiento_especializado(dolencia):
    """Busca conocimiento especializado relevante para la dolencia."""
    if not dolencia or not isinstance(dolencia, str):
        return ""
    
    dolencia_lower = dolencia.lower()
    conocimientos_encontrados = []
    
    for sistema, info in CONOCIMIENTO_ESPECIALIZADO.items():
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
        
        # PORTADA
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
        
        # SECCIÓN 1: DATOS DEL PACIENTE
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
        
        # SECCIÓN 2: DIAGNÓSTICO
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
        
        # SECCIÓN 3: INFORMACIÓN LEGAL
        story.append(Paragraph("INFORMACIÓN IMPORTANTE", estilo_subtitulo))
        
        legal_text = """
        <b>Confidencialidad:</b> Este documento contiene información confidencial del paciente. 
        Su distribución está limitada al paciente y profesionales de la salud involucrados en su tratamiento.
        
        <b>Propósito:</b> Este diagnóstico es una herramienta de apoyo para profesionales de salud mental 
        y no sustituye evaluación médica, diagnóstico clínico o tratamiento profesional.
        
        <b>Contacto:</b> Para consultas profesionales, contacte a través del sistema MINDGEEKCLINIC.
        
        <b>Fecha de generación:</b> {}
        
        <b>Sistema:</b> MINDGEEKCLINIC v6.0 - Triangulación Diagnóstica con Conocimiento Expandido
        """.format(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        
        story.append(Paragraph(legal_text, estilo_paciente))
        
        # GENERAR PDF
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
        
    except Exception as e:
        st.error(f"Error al generar PDF: {str(e)}")
        return None

def guardar_paciente(datos):
    """Guarda datos del paciente en session_state."""
    if "pacientes" not in st.session_state:
        st.session_state.pacientes = []
    
    datos["fecha"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    datos["id"] = f"{datos['iniciales']}_{len(st.session_state.pacientes)+1:03d}"
    st.session_state.pacientes.append(datos)
    return datos["id"]

def formulario_diagnostico():
    """Muestra formulario clínico estructurado."""
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
        
        # DIAGNÓSTICO MÉDICO OPCIONAL
        st.markdown("---")
        st.markdown("#### 🏥 **INFORMACIÓN MÉDICA (OPCIONAL)**")
        
        diagnostico_medico = st.text_area(
            "**Diagnóstico médico recibido (si aplica):**",
            height=80,
            placeholder="""Ejemplo: 
- Diagnóstico: Gastritis crónica tipo B
- Tratamiento: Omeprazol 40mg/día
- Estudios realizados: Endoscopia digestiva alta
- Especialista: Dr. González, Gastroenterólogo

O déjelo en blanco si no tiene diagnóstico médico formal.""",
            help="Este campo es completamente opcional."
        )
        
        st.markdown("---")
        st.markdown("#### 🎯 **EVENTOS EMOCIONALES ASOCIADOS (TRIANGULACIÓN)**")
        
        st.markdown("**Pregunta clave:** ¿Qué eventos suceden en su vida que impactan emocionalmente CUANDO se presenta el cuadro?")
        
        eventos_emocionales = st.text_area(
            "Describa los eventos específicos:",
            height=150,
            placeholder="""Ejemplo detallado:
1. El síntoma empeora los lunes cuando voy a trabajar
2. Aparece después de discusiones con mi pareja
3. Se intensifica cuando visito a mis padres
4. Mejora cuando estoy de vacaciones
5. Comenzó después de la muerte de mi padre hace 2 años

Describa la RELACIÓN TEMPORAL entre eventos y síntomas:"""
        )
        
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
        
        st.markdown("---")
        st.markdown("#### 👥 **ENTORNO SOCIAL ACTUAL**")
        entorno_social = st.text_area(
            "Describa su entorno social actual:",
            height=100,
            placeholder="Ej: Vivo solo después de divorcio, tengo 2 hijos, pocos amigos cercanos, relación conflictiva con jefe..."
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

def generar_diagnostico_triangulacion(sistema, datos_paciente):
    """Genera diagnóstico completo con triangulación."""
    
    conocimiento_especializado = buscar_conocimiento_especializado(datos_paciente['dolencia'])
    
    diagnostico_medico_texto = ""
    if datos_paciente.get('diagnostico_medico') and datos_paciente['diagnostico_medico'].strip():
        diagnostico_medico_texto = f"""
        **DIAGNÓSTICO MÉDICO PREVIO:**
        {datos_paciente['diagnostico_medico']}
        
        **INSTRUCCIÓN ESPECÍFICA:** Integrar este diagnóstico médico en el análisis de biodescodificación.
        """
    
    prompt = f"""
    ## 🧠 DIAGNÓSTICO DE BIODESCODIFICACIÓN CON TRIANGULACIÓN - MINDGEEKCLINIC v6.0
    
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
    
    **SÍNTOMA PRINCIPAL:**
    {datos_paciente['dolencia']}
    
    **EVENTOS EMOCIONALES ASOCIADOS (PARA TRIANGULACIÓN):**
    {datos_paciente['eventos_emocionales']}
    
    **FACTORES DESENCADENANTES:**
    {datos_paciente['factores_desencadenantes']}
    
    **ENTORNO SOCIAL:**
    {datos_paciente['entorno_social']}
    
    **CONOCIMIENTO ESPECIALIZADO RELEVANTE:**
    {conocimiento_especializado if conocimiento_especializado else "Basándose en la base de conocimientos completa."}
    
    **INSTRUCCIONES ESPECÍFICAS PARA EL ASISTENTE:**
    
    1. **CONSULTAR LA BASE DE CONOCIMIENTOS COMPLETA:**
       - Base principal + Conocimiento especializado de Google Drive
       - Incluir referencias de ambos sistemas de conocimiento
       - Priorizar información más reciente y especializada
    
    2. **TRIANGULACIÓN DIAGNÓSTICA:**
       - Analizar relación temporal eventos-síntomas
       - Identificar patrones específicos
       - Relacionar tiempo del padecimiento con eventos de vida
    
    3. **INTEGRAR DIAGNÓSTICO MÉDICO (si aplica):**
       - Considerar diagnóstico médico como contexto valioso
       - Proporcionar perspectiva complementaria
    
    4. **DIAGNÓSTICO ESPECÍFICO:**
       - Interpretar la dolencia según biodescodificación
       - Identificar CONFLICTO EMOCIONAL PRECISO
       - Explicar SIGNIFICADO BIOLÓGICO
    
    5. **PROTOCOLO TERAPÉUTICO ESTRUCTURADO (3 SESIONES):**
       - SESIÓN 1: Enfoque en [conflicto específico]
       - SESIÓN 2: Trabajo en [eventos emocionales clave]
       - SESIÓN 3: Integración y estrategias específicas
    
    6. **PROTOCOLO DE HIPNOSIS ESPECÍFICO:**
       - Basado en biblioteca de modelos
       - Frecuencia: 3 veces por semana
       - Duración: 15-20 minutos
       - Técnicas ESPECÍFICAS
    
    7. **RECOMENDACIONES PERSONALIZADAS:**
       - Basadas en triangulación
       - Ejercicios específicos
       - Estrategias prácticas
    
    **FORMATO DE RESPUESTA:**
    
    ## 🔍 DIAGNÓSTICO POR TRIANGULACIÓN (CON BASE EXPANDIDA)
    
    ### 1. Análisis con Conocimiento Expandido
    [Incluir referencias de base principal + Drive]
    
    ### 2. Patrones de Triangulación Identificados
    [Relación eventos-síntomas]
    
    ### 3. Contexto Médico
    [Si aplica]
    
    ### 4. Diagnóstico de Biodescodificación
    [Conflicto emocional + significado biológico]
    
    ### 5. Protocolo de 3 Sesiones
    Sesión 1: [Instrucciones]
    Sesión 2: [Instrucciones]
    Sesión 3: [Instrucciones]
    
    ### 6. Protocolo de Hipnosis
    [Instrucciones DETALLADAS]
    
    ### 7. Recomendaciones Específicas
    [Basadas en análisis completo]
    
    **RESPUESTA PROFESIONAL ESTRUCTURADA:**
    """
    
    try:
        respuesta = sistema.invoke({"query": prompt})
        return respuesta['result']
    except Exception as e:
        return f"Error al generar diagnóstico: {str(e)}"

def generar_guion_hipnosis(sistema, datos_paciente, tipo="terapeuta"):
    """Genera guión específico de hipnosis."""
    
    tipo_texto = "para aplicación por terapeuta" if tipo == "terapeuta" else "para grabación de autohipnosis"
    
    prompt = f"""
    ## 🎧 GUION DE HIPNOSIS ESPECÍFICO - MINDGEEKCLINIC
    
    **CONTEXTO DEL PACIENTE:**
    - Síntoma: {datos_paciente['dolencia']}
    - Eventos emocionales: {datos_paciente['eventos_emocionales'][:200]}
    
    **INSTRUCCIONES:**
    Generar guión COMPLETO de hipnosis {tipo_texto} basado en la biblioteca completa.
    
    **ESTRUCTURA:**
    
    ### 🎯 OBJETIVO TERAPÉUTICO
    
    ### 📝 GUIÓN COMPLETO
    
    **INDUCCIÓN:**
    
    **TRABAJO TERAPÉUTICO:**
    
    **SUGERENCIAS POSHIPNÓTICAS:**
    
    **DESPERTAR:**
    
    ### 🕒 INSTRUCCIONES DE APLICACIÓN
    
    **GUIÓN COMPLETO:**
    """
    
    try:
        respuesta = sistema.invoke({"query": prompt})
        return respuesta['result']
    except Exception as e:
        return f"Error al generar guión: {str(e)}"

@st.cache_resource
def cargar_sistema_completo():
    """Carga el sistema RAG con biblioteca especializada y contenido de Drive."""
    
    # Verificar que la API Key está configurada
    if not GROQ_API_KEY:
        st.error("❌ GROQ_API_KEY no configurada en secrets.toml")
        st.info("""
        **Cómo configurar:**
        1. Crea/edita `.streamlit/secrets.toml`
        2. Añade: GROQ_API_KEY = "tu_api_key_aqui"
        3. Reinicia la aplicación
        """)
        return None
    
    with st.spinner("🔄 Cargando sistema especializado con conocimiento expandido..."):
        try:
            # ===== 1. CARGAR BASE PRINCIPAL =====
            response = requests.get(ZIP_URL, stream=True, timeout=60)
            if response.status_code != 200:
                st.error(f"❌ Error al descargar biblioteca principal.")
                return None
            
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "biblioteca.zip")
            extract_path = os.path.join(temp_dir, "biodescodificacion_db")
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            
            # ===== 2. CONFIGURAR EMBEDDINGS Y VECTOR STORE =====
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            vector_store = Chroma(
                persist_directory=extract_path,
                embedding_function=embeddings
            )
            
            # ===== 3. CARGAR CONOCIMIENTO DE DRIVE =====
            st.info("🌐 Conectando con Google Drive para conocimiento avanzado...")
            documentos_drive = cargar_documentos_drive(GOOGLE_DRIVE_URL)
            
            if documentos_drive:
                if enriquecer_base_conocimientos(vector_store, documentos_drive):
                    st.success("✅ Sistema cargado con conocimiento expandido")
                else:
                    st.info("ℹ️ Usando solo base principal")
            else:
                st.info("ℹ️ No se cargó conocimiento adicional de Drive")
            
            # ===== 4. CONFIGURAR LLM Y CHAIN =====
            llm = ChatGroq(
                groq_api_key=GROQ_API_KEY,
                model_name="meta-llama/llama-4-scout-17b-16e-instruct",
                temperature=0.3,
                max_tokens=3500
            )
            
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=vector_store.as_retriever(search_kwargs={"k": 12}),
                return_source_documents=True,
                verbose=False
            )
            
            return qa_chain
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)[:200]}")
            return None

# ================= INTERFAZ PRINCIPAL =================
st.set_page_config(
    page_title="MINDGEEKCLINIC - Biodescodificación con Conocimiento Expandido",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/271/271226.png", width=80)
    st.markdown("### 🏥 MINDGEEKCLINIC")
    st.markdown("**v6.0 con Base de Conocimientos Expandida**")
    st.markdown("---")
    
    st.markdown("#### 📊 Estadísticas")
    if "pacientes" in st.session_state:
        st.metric("Pacientes atendidos", len(st.session_state.pacientes))
    
    st.markdown("---")
    
    # Indicador de conocimiento
    st.markdown("#### 🧠 Sistema de Conocimiento")
    st.markdown("✅ **Base principal** (ZIP)")
    st.markdown("✅ **Conocimiento Drive** (Actualizado)")
    st.markdown("✅ **Conocimiento especializado** (Diccionario)")
    
    st.markdown("---")
    
    if st.button("🆕 Nuevo Diagnóstico", use_container_width=True, type="primary"):
        st.session_state.mostrar_diagnostico = False
        st.session_state.generar_guion = False
        st.session_state.generar_grabacion = False
        st.session_state.pdf_generado = None
        st.session_state.diagnostico_completo = None
        st.rerun()
    
    if st.button("🔄 Recargar Conocimiento", use_container_width=True):
        st.cache_resource.clear()
        st.success("Conocimiento recargado")
        st.rerun()
    
    st.markdown("---")
    st.caption("🎯 Sistema con Triangulación + Conocimiento Expandido")

# Título principal
st.title("🧠 MINDGEEKCLINIC v6.0")
st.markdown("### **Sistema de Biodescodificación con Base de Conocimientos Expandida**")
st.markdown("*Integración de conocimiento especializado desde Google Drive para diagnósticos más precisos*")
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
    
    with st.expander("📋 Ver datos completos", expanded=True):
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
    
    # Mostrar conocimiento especializado aplicable
    conocimiento_especializado = buscar_conocimiento_especializado(paciente['dolencia'])
    if conocimiento_especializado:
        with st.expander("🔬 **Conocimiento Especializado Aplicable**", expanded=True):
            st.markdown(conocimiento_especializado)
    
    # Generar diagnóstico con triangulación
    st.markdown("---")
    st.markdown("### 🔬 **DIAGNÓSTICO CON CONOCIMIENTO EXPANDIDO**")
    
    if st.session_state.diagnostico_completo is None:
        with st.spinner("🔄 Analizando con base de conocimientos completa..."):
            diagnostico = generar_diagnostico_triangulacion(sistema, paciente)
            st.session_state.diagnostico_completo = diagnostico
    
    # Mostrar diagnóstico
    st.markdown(st.session_state.diagnostico_completo)
    
    # SECCIÓN DE HIPNOSIS
    st.markdown("---")
    st.markdown("### 🎧 **PROTOCOLOS DE HIPNOSIS**")
    
    if not st.session_state.generar_guion and not st.session_state.generar_grabacion:
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📝 Generar guión para terapeuta", use_container_width=True):
                st.session_state.generar_guion = True
                st.rerun()
        
        with col2:
            if st.button("🎤 Generar guión para GRABACIÓN", use_container_width=True):
                st.session_state.generar_grabacion = True
                st.rerun()
    
    # Generar guiones específicos
    if st.session_state.generar_guion:
        st.markdown("---")
        st.markdown("### 👨‍⚕️ **GUIÓN PARA TERAPEUTA**")
        with st.spinner("Generando guión..."):
            guion = generar_guion_hipnosis(sistema, paciente, "terapeuta")
            st.markdown(guion)
            
            if st.button("↩️ Volver", use_container_width=True):
                st.session_state.generar_guion = False
                st.rerun()
    
    if st.session_state.generar_grabacion:
        st.markdown("---")
        st.markdown("### 🎵 **GUIÓN PARA AUTOGRABACIÓN**")
        with st.spinner("Generando guión para grabación..."):
            guion = generar_guion_hipnosis(sistema, paciente, "grabacion")
            st.markdown(guion)
            
            if st.button("↩️ Volver", use_container_width=True):
                st.session_state.generar_grabacion = False
                st.rerun()
    
    # BOTÓN DE GUARDAR COMO PDF
    st.markdown("---")
    st.markdown("### 💾 **EXPORTAR DIAGNÓSTICO**")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if st.button("🆕 NUEVO diagnóstico", use_container_width=True, type="primary"):
            st.session_state.mostrar_diagnostico = False
            st.session_state.diagnostico_completo = None
            st.session_state.generar_guion = False
            st.session_state.generar_grabacion = False
            st.session_state.pdf_generado = None
            st.rerun()
    
    with col2:
        if st.button("📄 Generar PDF", use_container_width=True, type="secondary"):
            with st.spinner("🔄 Generando PDF..."):
                if st.session_state.paciente_actual and st.session_state.diagnostico_completo:
                    pdf_bytes = generar_pdf_diagnostico(
                        st.session_state.paciente_actual,
                        st.session_state.diagnostico_completo
                    )
                    
                    if pdf_bytes:
                        st.session_state.pdf_generado = pdf_bytes
                        st.success("✅ PDF generado")
                        
                        nombre_archivo = f"Diagnostico_{paciente['iniciales']}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                        
                        b64 = base64.b64encode(pdf_bytes).decode()
                        href = f'<a href="data:application/pdf;base64,{b64}" download="{nombre_archivo}" target="_blank">'
                        href += '<button style="background-color: #4CAF50; color: white; padding: 14px 28px; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; width: 100%; font-weight: bold;">📥 Descargar PDF</button>'
                        href += '</a>'
                        
                        st.markdown(href, unsafe_allow_html=True)
                    else:
                        st.error("❌ Error al generar PDF")
                else:
                    st.warning("⚠️ No hay diagnóstico para generar PDF")
    
    with col3:
        if st.button("ℹ️ Información", use_container_width=True):
            st.info("""
            **Sistema de Conocimiento:**
            - Base principal ZIP: Fundamentos teóricos
            - Google Drive: Conocimiento especializado actualizado
            - Diccionario especializado: Sistemas corporales específicos
            
            **Actualización:**
            - El sistema recarga conocimiento automáticamente
            - Añade nuevos documentos de Drive al reiniciar
            - Integra múltiples fuentes de conocimiento
            """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.8em;'>
    🧠 <b>MINDGEEKCLINIC v6.0</b> • Sistema con Conocimiento Expandido • 
    Base ZIP + Google Drive + Conocimiento Especializado • 
    Diagnósticos más precisos y profesionales
    </div>
    """,
    unsafe_allow_html=True
)
