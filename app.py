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
          
