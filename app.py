este es el app py
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
        st.error(f"
*************************
este es el requirements 
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
        st.error(f"
