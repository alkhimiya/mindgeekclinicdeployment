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

# ================= NUEVO: CONTADOR DE ACCESOS (ARCHIVO JSON) =================
COUNTER_FILE = Path("mindgeek_access_counter.json")

def update_access_counter(action="view"):
    """
    Actualiza el contador de accesos en un archivo JSON.
    action: 'view' (acceso a la app) o 'diagnostic' (PDF generado).
    """
    try:
        if COUNTER_FILE.exists():
            with open(COUNTER_FILE, 'r') as f:
                data = json.load(f)
        else:
            data = {"total_views": 0, "diagnostics_generated": 0, "last_updated": None}
        
        if action == "view":
            data["total_views"] += 1
        elif action == "diagnostic":
            data["diagnostics_generated"] += 1
        
        data["last_updated"] = datetime.now().isoformat()
        
        temp_file = COUNTER_FILE.with_suffix('.tmp')
        with open(temp_file, 'w') as f:
            json.dump(data, f, indent=4)
        temp_file.replace(COUNTER_FILE)
        
        return data
    except Exception as e:
        return {"total_views": "N/A", "diagnostics_generated": "N/A", "last_updated": None}

def load_counter_data():
    """Solo carga los datos del contador sin incrementar."""
    try:
        if COUNTER_FILE.exists():
            with open(COUNTER_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {"total_views": 0, "diagnostics_generated": 0, "last_updated": None}

# Contar cada vez que alguien abre la app
if 'view_counted' not in st.session_state:
    update_access_counter("view")
    st.session_state.view_counted = True
# ===================================================================

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
        
        # ============ TABLA BÁSICA CON DOLENCIA EN POSICIÓN CORRECTA ============
        datos_basicos = [
            ["<b>Estado Civil:</b>", datos_paciente['estado_civil']],
            ["<b>Situación Laboral:</b>", datos_paciente['situacion_laboral']],
            ["<b>Tensión Arterial:</b>", datos_paciente['tension']],
            ["<b>Dolencia/Síntoma Principal:</b>", datos_paciente['dolencia']],  # ← POSICIÓN 4
            ["<b>Tiempo Padecimiento:</b>", datos_paciente['tiempo_padecimiento']],  # ← POSICIÓN 5
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
                            spaceBefore=15,
                            spaceAfter=8,
                            alignment=TA_LEFT
                        )
                        seccion = seccion.replace('#', '').strip()
                        story.append(Paragraph(f"<b>{seccion}</b>", estilo))
                    else:
                        story.append(Paragraph(f"<b>{seccion}</b>", estilo_diagnostico))
                else:
                    story.append(Paragraph(seccion, estilo_diagnostico))
        
        # Construir el documento
        doc.build(story)
        
        # Obtener bytes del PDF
        buffer.seek(0)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        # Actualizar contador de diagnósticos generados
        update_access_counter("diagnostic")
        
        return pdf_bytes
    
    except Exception as e:
        st.error(f"Error al generar PDF: {str(e)}")
        return None

# ================= FUNCIONES PARA LA BASE DE DATOS VECTORIAL =================
@st.cache_resource
def descargar_y_cargar_bd():
    """
    Descarga el archivo ZIP de la base de datos vectorial y carga ChromaDB.
    """
    try:
        # Crear directorio temporal
        temp_dir = tempfile.mkdtemp()
        
        # Descargar el archivo ZIP
        st.info("Descargando base de datos de conocimiento...")
        response = requests.get(ZIP_URL, stream=True)
        response.raise_for_status()
        
        zip_path = os.path.join(temp_dir, "mindgeekclinic_db.zip")
        
        # Guardar el archivo ZIP
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Extraer el ZIP
        extract_dir = os.path.join(temp_dir, "extracted")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # Buscar el directorio de ChromaDB
        chroma_dir = None
        for root, dirs, files in os.walk(extract_dir):
            if "chroma.sqlite3" in files:
                chroma_dir = root
                break
        
        if not chroma_dir:
            raise Exception("No se encontró la base de datos vectorial en el archivo ZIP")
        
        # Cargar los embeddings
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        
        # Cargar ChromaDB
        vectorstore = Chroma(
            persist_directory=chroma_dir,
            embedding_function=embeddings
        )
        
        st.success("Base de datos cargada exitosamente!")
        return vectorstore
    
    except Exception as e:
        st.error(f"Error al cargar la base de datos: {str(e)}")
        return None

# ================= FUNCIÓN PARA OBTENER DIAGNÓSTICO =================
def obtener_diagnostico(vectorstore, pregunta, contexto_paciente):
    """
    Obtiene un diagnóstico utilizando el modelo Groq y la base de datos vectorial.
    """
    try:
        # Buscar conocimiento especializado
        conocimiento_especializado = buscar_conocimiento_especializado(pregunta)
        
        # Construir el prompt completo
        prompt_base = f"""
        Eres un experto en biodescodificación clínica. Analiza el siguiente caso:

        CONTEXTO DEL PACIENTE:
        {contexto_paciente}

        PREGUNTA/INQUIETUD:
        {pregunta}

        INSTRUCCIONES:
        1. Identifica los posibles conflictos emocionales relacionados con los síntomas.
        2. Relaciona los síntomas con eventos emocionales específicos.
        3. Proporciona una interpretación simbólica de la dolencia.
        4. Sugiere posibles vías de resolución emocional.
        5. Mantén un tono profesional y empático.
        
        IMPORTANTE: Incluye la información de "CONOCIMIENTO ESPECIALIZADO APLICABLE" solo si está disponible.
        
        ESTRUCTURA DE RESPUESTA:
        ### Análisis de Conflictos Emocionales
        [Análisis detallado]
        
        ### Interpretación Simbólica
        [Interpretación simbólica]
        
        ### Eventos Desencadenantes Probables
        [Eventos identificados]
        
        ### Vías de Resolución Emocional
        [Sugerencias específicas]
        
        ### Notas Clínicas
        [Consideraciones importantes]
        
        """
        
        # Agregar conocimiento especializado si existe
        if conocimiento_especializado:
            prompt_base += f"\n\n{conocimiento_especializado}\n\n"
        
        # Inicializar el modelo Groq
        llm = ChatGroq(
            temperature=0.7,
            groq_api_key=GROQ_API_KEY,
            model_name="mixtral-8x7b-32768",
            max_tokens=4000
        )
        
        # Crear la cadena de RetrievalQA
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
            return_source_documents=False
        )
        
        # Obtener la respuesta
        respuesta = qa_chain.invoke({"query": prompt_base})
        
        if isinstance(respuesta, dict) and "result" in respuesta:
            return respuesta["result"]
        else:
            return str(respuesta)
    
    except Exception as e:
        return f"Error al generar diagnóstico: {str(e)}"

# ================= INTERFAZ DE STREAMLIT =================
def main():
    st.set_page_config(
        page_title="MindGeekClinic - Biodescodificación",
        page_icon="🧠",
        layout="wide"
    )
    
    # Sidebar con información
    with st.sidebar:
        st.image("https://via.placeholder.com/300x100/1E3A8A/FFFFFF?text=MINDGEEKCLINIC", width=250)
        st.title("🧠 MindGeekClinic")
        st.markdown("Sistema Profesional de Biodescodificación")
        
        st.divider()
        
        # Mostrar contador de accesos
        counter_data = load_counter_data()
        st.markdown("### 📊 Estadísticas")
        st.markdown(f"**Accesos totales:** {counter_data.get('total_views', 0)}")
        st.markdown(f"**Diagnósticos generados:** {counter_data.get('diagnostics_generated', 0)}")
        
        if counter_data.get('last_updated'):
            last_update = datetime.fromisoformat(counter_data['last_updated'])
            st.caption(f"Última actualización: {last_update.strftime('%d/%m/%Y %H:%M')}")
        
        st.divider()
        
        st.markdown("### ℹ️ Instrucciones")
        st.markdown("""
        1. Complete todos los campos del paciente
        2. Describa la dolencia principal
        3. Proporcione información emocional relevante
        4. Genere el diagnóstico
        5. Descargue el informe en PDF
        """)
        
        st.divider()
        st.caption("© 2024 MindGeekClinic - Sistema de Biodescodificación")
    
    # Contenido principal
    st.title("🧠 MindGeekClinic - Sistema de Biodescodificación")
    st.markdown("### Análisis Profesional de Conflictos Emocionales y Salud")
    
    # Inicializar vectorstore en session_state si no existe
    if 'vectorstore' not in st.session_state:
        with st.spinner("Cargando base de datos de conocimiento..."):
            vectorstore = descargar_y_cargar_bd()
            if vectorstore:
                st.session_state.vectorstore = vectorstore
            else:
                st.error("No se pudo cargar la base de datos. Por favor, recargue la página.")
                st.stop()
    
    # Pestañas para la interfaz
    tab1, tab2 = st.tabs(["📋 Datos del Paciente", "📊 Diagnóstico"])
    
    with tab1:
        st.subheader("Información del Paciente")
        
        col1, col2 = st.columns(2)
        
        with col1:
            iniciales = st.text_input("Iniciales del Paciente*", max_length=10, 
                                    help="Ejemplo: MJR para María José Rodríguez")
            edad = st.number_input("Edad*", min_value=1, max_value=120, value=30)
            estado_civil = st.selectbox("Estado Civil*", 
                                       ["Soltero/a", "Casado/a", "Divorciado/a", "Viudo/a", "Unión Libre"])
            situacion_laboral = st.selectbox("Situación Laboral*",
                                            ["Empleado/a", "Desempleado/a", "Independiente", 
                                             "Estudiante", "Jubilado/a", "Ama de casa"])
            tension = st.text_input("Tensión Arterial", 
                                   help="Ejemplo: 120/80 mmHg o Sistólica/Diastólica")
        
        with col2:
            dolencia = st.text_area("Dolencia/Síntoma Principal*", 
                                   height=100,
                                   placeholder="Describa la dolencia o síntoma principal...")
            tiempo_padecimiento = st.text_input("Tiempo de Padecimiento*",
                                               placeholder="Ejemplo: 6 meses, 2 años, desde la infancia...")
            frecuencia = st.selectbox("Frecuencia*",
                                     ["Constante", "Diaria", "Semanal", "Mensual", 
                                      "Esporádica", "Solo en crisis"])
            intensidad = st.slider("Intensidad (0-10)*", 0, 10, 5,
                                  help="0 = Sin dolor, 10 = Dolor insoportable")
            diagnostico_medico = st.text_input("Diagnóstico Médico (si existe)",
                                              placeholder="Ejemplo: Migraña crónica, Gastritis, etc.")
        
        st.divider()
        
        st.subheader("Información Emocional y Contextual")
        
        col3, col4 = st.columns(2)
        
        with col3:
            factores_desencadenantes = st.text_area("Factores Desencadenantes Identificados",
                                                   height=100,
                                                   placeholder="Eventos, situaciones o factores que empeoran o desencadenan los síntomas...")
        
        with col4:
            eventos_emocionales = st.text_area("Eventos Emocionales Asociados*",
                                              height=100,
                                              placeholder="Eventos emocionales significativos antes o durante el padecimiento...")
        
        entorno_social = st.text_area("Entorno Social y Relacional*",
                                     height=100,
                                     placeholder="Descripción del entorno familiar, laboral, social y relaciones significativas...")
        
        # Guardar datos en session_state
        if st.button("💾 Guardar Datos del Paciente", type="primary", use_container_width=True):
            if not all([iniciales, dolencia, tiempo_padecimiento, eventos_emocionales, entorno_social]):
                st.warning("Por favor, complete todos los campos obligatorios (*)")
            else:
                st.session_state.datos_paciente = {
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
                st.success("Datos del paciente guardados correctamente!")
    
    with tab2:
        st.subheader("Generar Diagnóstico de Biodescodificación")
        
        if 'datos_paciente' not in st.session_state:
            st.warning("Por favor, complete y guarde primero los datos del paciente en la pestaña anterior.")
        else:
            datos_paciente = st.session_state.datos_paciente
            
            # Mostrar resumen de datos
            with st.expander("📋 Ver Datos del Paciente Guardados"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Iniciales:** {datos_paciente['iniciales']}")
                    st.markdown(f"**Edad:** {datos_paciente['edad']} años")
                    st.markdown(f"**Estado Civil:** {datos_paciente['estado_civil']}")
                    st.markdown(f"**Situación Laboral:** {datos_paciente['situacion_laboral']}")
                    if datos_paciente['tension']:
                        st.markdown(f"**Tensión Arterial:** {datos_paciente['tension']}")
                
                with col2:
                    st.markdown(f"**Dolencia Principal:** {datos_paciente['dolencia']}")
                    st.markdown(f"**Tiempo Padecimiento:** {datos_paciente['tiempo_padecimiento']}")
                    st.markdown(f"**Frecuencia:** {datos_paciente['frecuencia']}")
                    st.markdown(f"**Intensidad:** {datos_paciente['intensidad']}/10")
                    if datos_paciente.get('diagnostico_medico'):
                        st.markdown(f"**Diagnóstico Médico:** {datos_paciente['diagnostico_medico']}")
            
            # Construir el contexto del paciente para el diagnóstico
            contexto_paciente = f"""
            DATOS DEMOGRÁFICOS:
            - Iniciales: {datos_paciente['iniciales']}
            - Edad: {datos_paciente['edad']} años
            - Estado Civil: {datos_paciente['estado_civil']}
            - Situación Laboral: {datos_paciente['situacion_laboral']}
            - Tensión Arterial: {datos_paciente['tension']}
            
            DOLENCIA:
            - Síntoma Principal: {datos_paciente['dolencia']}
            - Tiempo de Padecimiento: {datos_paciente['tiempo_padecimiento']}
            - Frecuencia: {datos_paciente['frecuencia']}
            - Intensidad: {datos_paciente['intensidad']}/10
            - Diagnóstico Médico: {datos_paciente.get('diagnostico_medico', 'No especificado')}
            
            FACTORES EMOCIONALES:
            - Factores Desencadenantes: {datos_paciente.get('factores_desencadenantes', 'No especificados')}
            - Eventos Emocionales: {datos_paciente['eventos_emocionales']}
            
            CONTEXTO SOCIAL:
            - Entorno Social: {datos_paciente['entorno_social']}
            """
            
            # Botón para generar diagnóstico
            if st.button("🔍 Generar Diagnóstico de Biodescodificación", type="primary", use_container_width=True):
                with st.spinner("Analizando caso y generando diagnóstico..."):
                    diagnostico = obtener_diagnostico(
                        st.session_state.vectorstore,
                        datos_paciente['dolencia'],
                        contexto_paciente
                    )
                    
                    if diagnostico:
                        st.session_state.diagnostico = diagnostico
                        
                        # Mostrar el diagnóstico
                        st.subheader("📋 Diagnóstico de Biodescodificación")
                        st.markdown(diagnostico)
                        
                        # Generar y ofrecer descarga del PDF
                        with st.spinner("Generando informe PDF..."):
                            pdf_bytes = generar_pdf_diagnostico(datos_paciente, diagnostico)
                            
                            if pdf_bytes:
                                # Crear botón de descarga
                                b64_pdf = base64.b64encode(pdf_bytes).decode()
                                href = f'<a href="data:application/octet-stream;base64,{b64_pdf}" download="diagnostico_{datos_paciente["iniciales"]}_{datetime.now().strftime("%Y%m%d")}.pdf">📥 Descargar Diagnóstico en PDF</a>'
                                st.markdown(href, unsafe_allow_html=True)
                                st.success("Diagnóstico generado exitosamente!")
            
            # Mostrar diagnóstico si ya fue generado
            if 'diagnostico' in st.session_state:
                st.divider()
                st.subheader("📋 Diagnóstico Generado")
                st.markdown(st.session_state.diagnostico)
                
                # Botón para regenerar PDF
                if st.button("🔄 Regenerar PDF", use_container_width=True):
                    with st.spinner("Generando nuevo PDF..."):
                        pdf_bytes = generar_pdf_diagnostico(datos_paciente, st.session_state.diagnostico)
                        
                        if pdf_bytes:
                            b64_pdf = base64.b64encode(pdf_bytes).decode()
                            href = f'<a href="data:application/octet-stream;base64,{b64_pdf}" download="diagnostico_{datos_paciente["iniciales"]}_{datetime.now().strftime("%Y%m%d")}.pdf">📥 Descargar Diagnóstico en PDF</a>'
                            st.markdown(href, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
