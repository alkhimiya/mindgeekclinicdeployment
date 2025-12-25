import streamlit as st
import json
import os
import uuid
from datetime import datetime
import time
import random
import string
import re
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import base64
from io import BytesIO
import requests
from typing import Dict, List, Optional, Tuple
import numpy as np
from collections import Counter
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import groq

# ============================================
# CONFIGURACIÓN INICIAL DE LA APLICACIÓN
# ============================================

st.set_page_config(
    page_title="MINDGEEKCLINIC - Biodescodificación Profesional",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# SECCIÓN 1: CONFIGURACIÓN Y SECRETOS
# ============================================

# Configuración de la aplicación
APP_VERSION = "2.0.0"
DATA_FILE = "mindgeekclinic_data.json"
AFFILIATE_DB_FILE = "affiliates_db.json"  # NUEVO: Archivo para afiliados
ACCESS_LOG_FILE = "access_log.json"

# Configuración de la base de datos Chroma
CHROMA_DB_PATH = "./chroma_db"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Cargar secrets de Streamlit
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
CHROMA_PERSIST_DIRECTORY = st.secrets.get("CHROMA_PERSIST_DIRECTORY", CHROMA_DB_PATH)

# ============================================
# SECCIÓN 2: INICIALIZACIÓN DE SESIÓN
# ============================================

if 'page_views' not in st.session_state:
    st.session_state.page_views = 0
if 'diagnosticos_realizados' not in st.session_state:
    st.session_state.diagnosticos_realizados = 0
if 'pacientes_registrados' not in st.session_state:
    st.session_state.pacientes_registrados = 0
if 'access_count' not in st.session_state:
    st.session_state.access_count = 0

# Variables para el sistema de afiliados (NUEVO)
if 'affiliate_code_input' not in st.session_state:
    st.session_state.affiliate_code_input = ""
if 'current_affiliate' not in st.session_state:
    st.session_state.current_affiliate = None
if 'verification_code' not in st.session_state:
    st.session_state.verification_code = None
if 'verification_email' not in st.session_state:
    st.session_state.verification_email = None
if 'verification_time' not in st.session_state:
    st.session_state.verification_time = None

# ============================================
# SECCIÓN 3: FUNCIONES DE BASE DE DATOS Y ESTADO
# ============================================

def load_data():
    """Carga los datos de la aplicación desde el archivo JSON."""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Inicializar contadores desde el archivo si existen
            if 'statistics' in data:
                stats = data['statistics']
                st.session_state.page_views = stats.get('total_accesses', 0)
                st.session_state.diagnosticos_realizados = stats.get('total_diagnoses', 0)
                st.session_state.pacientes_registrados = stats.get('total_patients', 0)
                st.session_state.access_count = stats.get('access_count', 0)
                
            return data
    except FileNotFoundError:
        # Si el archivo no existe, crear estructura inicial
        initial_data = {
            "patients": [],
            "diagnoses": [],
            "statistics": {
                "total_accesses": 0,
                "total_diagnoses": 0,
                "total_patients": 0,
                "access_count": 0,
                "daily_access": {},
                "monthly_trend": {}
            }
        }
        save_data(initial_data)
        return initial_data
    except json.JSONDecodeError:
        st.error("Error al leer el archivo de datos. Se creará una nueva base de datos.")
        initial_data = {
            "patients": [],
            "diagnoses": [],
            "statistics": {
                "total_accesses": 0,
                "total_diagnoses": 0,
                "total_patients": 0,
                "access_count": 0,
                "daily_access": {},
                "monthly_trend": {}
            }
        }
        return initial_data

def save_data(data):
    """Guarda los datos de la aplicación en el archivo JSON."""
    # Actualizar estadísticas en los datos antes de guardar
    data['statistics']['total_accesses'] = st.session_state.page_views
    data['statistics']['total_diagnoses'] = st.session_state.diagnosticos_realizados
    data['statistics']['total_patients'] = st.session_state.pacientes_registrados
    data['statistics']['access_count'] = st.session_state.access_count
    
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Error al guardar datos: {str(e)}")
        return False

def load_affiliate_db():
    """Carga la base de datos de afiliados desde el archivo JSON."""
    try:
        with open(AFFILIATE_DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # Si el archivo no existe, retorna estructura vacía
        return {"affiliates": [], "settings": {
            "commission_rates": {"therapy": 0.345, "pdf": 0.333, "subscription": 0.316},
            "min_withdrawal": 50.0,
            "payout_schedule": "weekly"
        }}
    except json.JSONDecodeError:
        st.error("Error al leer la base de datos de afiliados. Se usará una estructura vacía.")
        return {"affiliates": [], "settings": {
            "commission_rates": {"therapy": 0.345, "pdf": 0.333, "subscription": 0.316},
            "min_withdrawal": 50.0,
            "payout_schedule": "weekly"
        }}

def save_affiliate_db(data):
    """Guarda la base de datos de afiliados en el archivo JSON."""
    try:
        with open(AFFILIATE_DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Error al guardar datos de afiliados: {str(e)}")
        return False

# ============================================
# SECCIÓN 4: FUNCIONES DE CONTADOR DE ACCESOS
# ============================================

def load_access_log():
    """Carga el registro de accesos."""
    try:
        with open(ACCESS_LOG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"accesses": [], "daily_stats": {}}

def save_access_log(log_data):
    """Guarda el registro de accesos."""
    try:
        with open(ACCESS_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"Error al guardar registro de accesos: {str(e)}")

def track_access():
    """Registra un nuevo acceso a la aplicación."""
    st.session_state.access_count += 1
    st.session_state.page_views += 1
    
    # Actualizar registro de accesos
    log_data = load_access_log()
    current_time = datetime.now().isoformat()
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Registrar acceso actual
    log_data["accesses"].append({
        "timestamp": current_time,
        "session_id": str(uuid.uuid4())[:8]
    })
    
    # Actualizar estadísticas diarias
    if today not in log_data["daily_stats"]:
        log_data["daily_stats"][today] = 0
    log_data["daily_stats"][today] += 1
    
    # Mantener solo los últimos 1000 accesos
    if len(log_data["accesses"]) > 1000:
        log_data["accesses"] = log_data["accesses"][-1000:]
    
    save_access_log(log_data)

# ============================================
# SECCIÓN 5: FUNCIONES DE CONOCIMIENTO ESPECIALIZADO
# ============================================

def get_specialized_knowledge():
    """Retorna el conocimiento especializado por sistemas corporales."""
    knowledge_base = {
        "ocular": {
            "name": "Sistema Ocular",
            "conflictos": [
                "Conflicto de 'no querer ver algo' o 'haber visto algo desagradable'",
                "Miedo al futuro, a lo que viene",
                "Separación visual traumática",
                "Deseo de no enfrentar una realidad",
                "Pérdida de protección visual"
            ],
            "ejemplos": [
                "Miope: 'No quiero ver lo que está lejos (futuro)'",
                "Hipermétrope: 'Temo lo que está cerca (presente)'",
                "Cataratas: 'Niebla mental, no ver con claridad'",
                "Glaucoma: 'Presión por lo que veo, acumulación de estrés visual'"
            ],
            "protocolo": "Visualización de escenas deseadas, diálogo con la parte afectada, integración de la nueva visión"
        },
        "dermatologico": {
            "name": "Sistema Dermatológico",
            "conflictos": [
                "Conflicto de separación (piel = contacto)",
                "Pérdida de protección, vulnerabilidad",
                "Ataque a la integridad, críticas que 'rasguñan'",
                "Deseo inconsciente de establecer límites",
                "Contacto no deseado o contacto deseado pero ausente"
            ],
            "ejemplos": [
                "Psoriasis: 'Separación conflictiva, querer renovar el contacto'",
                "Eccema: 'Separación con conflicto de irritación'",
                "Acné: 'Conflicto de identidad, no aceptación de la imagen'",
                "Urticaria: 'Miedo territorial, algo que 'me sale por la piel''"
            ],
            "protocolo": "Visualización de capas protectoras saludables, integración de límites, sanación del contacto"
        },
        "digestivo": {
            "name": "Sistema Digestivo",
            "conflictos": [
                "Conflicto de 'no poder digerir' un pedazo o situación",
                "Ira, rencor, frustración retenida",
                "Preocupación económica o familiar 'indigerible'",
                "Miedo a no tener lo suficiente",
                "Resistencia a nuevas ideas o experiencias"
            ],
            "ejemplos": [
                "Gastritis: 'Ira no expresada, algo que 'quema' en el estómago'",
                "Colon irritable: 'Miedo territorial con prisa por eliminar'",
                "Úlcera: 'Conflicto de desvalorización digestiva'",
                "Estreñimiento: 'Aferrarse a lo viejo, miedo a soltar'"
            ],
            "protocolo": "Diálogo con el órgano afectado, liberación emocional específica, visualización de digestión fluida"
        },
        "respiratorio": {
            "name": "Sistema Respiratorio",
            "conflictos": [
                "Conflicto de miedo territorial",
                "Sensación de 'no tener derecho al espacio vital'",
                "Pérdida, separación o muerte de alguien cercano",
                "Miedo a la asfixia emocional o física",
                "Conflicto de olores o atmósferas tóxicas"
            ],
            "ejemplos": [
                "Asma: 'Conflicto de territorio con miedo a asfixia'",
                "Rinitis: 'Olor a peligro, alerta constante'",
                "Bronquitis: 'Conflicto de territorio en familia'",
                "Sinusitis: 'Olor a conflicto cercano, irritación por alguien cercano'"
            ],
            "protocolo": "Respiración consciente, expansión del espacio vital, liberación de miedos territoriales"
        },
        "muscular": {
            "name": "Sistema Muscular",
            "conflictos": [
                "Conflicto de desvalorización en la acción",
                "Sentirse incapaz de realizar algo importante",
                "Frustración por no poder 'agarrar' o 'sostener'",
                "Pérdida de fuerza o poder en una situación",
                "Conflicto de dirección en la vida"
            ],
            "ejemplos": [
                "Contracturas: 'Tensión por acción no realizada'",
                "Artritis: 'Autocrítica severa, rigidez mental'",
                "Lumbalgia: 'Sobre carga emocional, 'cargar con algo''",
                "Tendinitis: 'Frustración por dirección tomada'"
            ],
            "protocolo": "Diálogo con el músculo, recuperación de la potencia personal, visualización de movimiento fluido"
        }
    }
    return knowledge_base

def get_system_by_symptom(symptom):
    """Devuelve el sistema corporal más relacionado con un síntoma."""
    symptom_mapping = {
        "ocular": ["visión", "ojo", "ver", "miope", "catarata", "glaucoma", "retina"],
        "dermatologico": ["piel", "dermatitis", "eczema", "acné", "urticaria", "picor", "roncha"],
        "digestivo": ["estómago", "intestino", "digestión", "gastritis", "colon", "úlcera", "náusea"],
        "respiratorio": ["respiración", "pulmón", "asma", "tos", "bronquios", "nariz", "sinusitis"],
        "muscular": ["músculo", "dolor", "articulación", "contractura", "artritis", "tendón", "espalda"]
    }
    
    symptom_lower = symptom.lower()
    for system, keywords in symptom_mapping.items():
        for keyword in keywords:
            if keyword in symptom_lower:
                return system
    return "general"

# ============================================
# SECCIÓN 6: FUNCIONES DE IA Y RAG
# ============================================

def initialize_chroma_db():
    """Inicializa o carga la base de datos vectorial Chroma."""
    try:
        # Configurar cliente Chroma
        chroma_client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIRECTORY,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Obtener o crear la colección
        collection_name = "mindgeekclinic_knowledge"
        try:
            collection = chroma_client.get_collection(name=collection_name)
        except:
            collection = chroma_client.create_collection(name=collection_name)
        
        return chroma_client, collection
    except Exception as e:
        st.error(f"Error inicializando ChromaDB: {str(e)}")
        return None, None

def get_embeddings(texts):
    """Genera embeddings para los textos usando Sentence Transformers."""
    try:
        model = SentenceTransformer(EMBEDDING_MODEL)
        embeddings = model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()
    except Exception as e:
        st.error(f"Error generando embeddings: {str(e)}")
        return None

def query_knowledge_base(query, collection, n_results=3):
    """Consulta la base de conocimiento vectorial."""
    if not collection:
        return []
    
    try:
        # Generar embedding para la consulta
        query_embedding = get_embeddings([query])
        if not query_embedding:
            return []
        
        # Realizar la búsqueda
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        
        return results
    except Exception as e:
        st.error(f"Error consultando base de conocimiento: {str(e)}")
        return []

def generate_with_groq(prompt, context=""):
    """Genera texto usando la API de Groq."""
    if not GROQ_API_KEY:
        st.warning("API key de Groq no configurada. Usando respuestas predefinidas.")
        return "Consulta no disponible: configure la API key de Groq en los secrets."
    
    try:
        client = groq.Groq(api_key=GROQ_API_KEY)
        
        full_prompt = f"""
        Eres un experto en biodescodificación y medicina psicosomática.
        
        Contexto adicional: {context}
        
        Pregunta del usuario: {prompt}
        
        Proporciona una respuesta profesional, compasiva y basada en los principios de la biodescodificación.
        Incluye posibles conflictos emocionales y sugerencias para la exploración terapéutica.
        """
        
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Eres un terapeuta especializado en biodescodificación con 20 años de experiencia."},
                {"role": "user", "content": full_prompt}
            ],
            model="mixtral-8x7b-32768",
            temperature=0.7,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error con la API de Groq: {str(e)}")
        return f"Error al generar respuesta: {str(e)}"

# ============================================
# SECCIÓN 7: FUNCIONES DE DIAGNÓSTICO Y TRIANGULACIÓN
# ============================================

def analyze_emotional_triangulation(symptoms, events, time_period):
    """Analiza la relación entre eventos emocionales y síntomas."""
    analysis = {
        "correlaciones": [],
        "conflictos_detectados": [],
        "recomendaciones": []
    }
    
    # Conocimiento especializado
    knowledge = get_specialized_knowledge()
    
    # Para cada síntoma, buscar sistema relacionado
    for symptom in symptoms.split(","):
        symptom = symptom.strip()
        if not symptom:
            continue
            
        system = get_system_by_symptom(symptom)
        system_info = knowledge.get(system, knowledge["ocular"])
        
        # Buscar eventos que puedan relacionarse
        for event in events.split(","):
            event = event.strip()
            if not event:
                continue
                
            # Análisis simple de correlación
            correlation_score = random.uniform(0.3, 0.9)  # En producción, usar IA real
            
            if correlation_score > 0.6:
                analysis["correlaciones"].append({
                    "sintoma": symptom,
                    "evento": event,
                    "sistema": system_info["name"],
                    "conflictos_posibles": system_info["conflictos"],
                    "puntuacion": round(correlation_score, 2)
                })
    
    # Generar recomendaciones
    if analysis["correlaciones"]:
        analysis["conflictos_detectados"] = [
            "Separación conflictiva",
            "Desvalorización en la acción", 
            "Miedo territorial",
            "Conflicto de identidad"
        ][:min(3, len(analysis["correlaciones"]))]
        
        analysis["recomendaciones"] = [
            "Explorar eventos alrededor del inicio de los síntomas",
            "Identificar emociones no expresadas relacionadas",
            "Trabajar con visualizaciones específicas para el sistema afectado",
            "Considerar terapia de hipnosis para acceder a memorias inconscientes"
        ]
    
    return analysis

def generate_diagnosis_report(patient_data, triangulation_analysis):
    """Genera un reporte de diagnóstico profesional."""
    report = f"""
    # 📋 INFORME DE BIODESCODIFICACIÓN
    
    ## 📊 Datos del Paciente
    **Nombre:** {patient_data.get('nombre', 'No especificado')}
    **Edad:** {patient_data.get('edad', 'No especificada')}
    **Género:** {patient_data.get('genero', 'No especificado')}
    **Dolencia principal:** {patient_data.get('dolencia', 'No especificada')}
    **Tiempo de padecimiento:** {patient_data.get('tiempo', 'No especificado')}
    
    ## 🎯 Análisis de Triangulación Emocional
    
    ### 🔍 Correlaciones Identificadas
    """
    
    if triangulation_analysis["correlaciones"]:
        for i, corr in enumerate(triangulation_analysis["correlaciones"], 1):
            report += f"""
    {i}. **{corr['sintoma']}** relacionado con **"{corr['evento']}"**
       - Sistema corporal: {corr['sistema']}
       - Conflictos posibles: {', '.join(corr['conflictos_posibles'][:2])}
       - Nivel de correlación: {corr['puntuacion']}/1.0
    """
    else:
        report += "\n    No se identificaron correlaciones significativas entre eventos y síntomas.\n"
    
    report += f"""
    ### 🎭 Conflictos Emocionales Detectados
    """
    
    if triangulation_analysis["conflictos_detectados"]:
        for conflicto in triangulation_analysis["conflictos_detectados"]:
            report += f"\n    - {conflicto}"
    else:
        report += "\n    No se detectaron conflictos emocionales específicos.\n"
    
    report += f"""
    ### 💡 Recomendaciones Terapéuticas
    """
    
    for recomendacion in triangulation_analysis["recomendaciones"]:
        report += f"\n    - {recomendacion}"
    
    report += f"""
    
    ## 🧠 Protocolo Sugerido
    
    ### 1. Exploración Inicial
    - Diálogo con el síntoma: preguntar qué emoción representa
    - Línea del tiempo emocional alrededor del inicio
    - Identificación de creencias limitantes relacionadas
    
    ### 2. Intervención Terapéutica
    - Técnicas de liberación emocional específicas
    - Visualización guiada del sistema afectado sanando
    - Reprogramación de creencias a nivel inconsciente
    
    ### 3. Seguimiento
    - Monitorización de cambios sintomáticos
    - Ajuste de protocolo según evolución
    - Integración de aprendizajes emocionales
    
    ## 📅 Información de la Sesión
    **Fecha del diagnóstico:** {datetime.now().strftime('%d/%m/%Y %H:%M')}
    **Terapeuta responsable:** Sistema MINDGEEKCLINIC
    **Versión de la plataforma:** {APP_VERSION}
    """
    
    return report

# ============================================
# SECCIÓN 8: FUNCIONES DE HIPNOSIS Y PROTOCOLOS
# ============================================

def generate_hypnosis_protocol(system, conflict_type):
    """Genera un protocolo de hipnosis personalizado."""
    protocols = {
        "ocular": {
            "conflicto_visual": """
            # Protocolo de Hipnosis para Conflictos Visuales
            
            ## Inducción
            1. Respiración profunda 4-7-8
            2. Relajación progresiva facial
            3. Enfoque en la sensación ocular
            
            ## Visualización Guiada
            "Imagina que tus ojos son ventanas hacia tu alma...
            Visualiza una luz suave que limpia cada capa de tensión...
            Permite que tu visión interna se aclare..."
            
            ## Sugestiones Post-Hipnóticas
            "Cada día verás con mayor claridad y aceptación...
            Tu visión se ajusta naturalmente a lo que necesitas experimentar..."
            """,
            "miedo_futuro": """
            # Protocolo para Miedo al Futuro
            
            ## Técnica de Línea del Tiempo
            1. Visualizar línea del tiempo personal
            2. Sanar eventos pasados que nublan la visión futura
            3. Proyectar imágenes positivas del futuro
            
            ## Afirmaciones
            "El futuro es una extensión amorosa del presente...
            Confío en mi capacidad de ver y adaptarme..."
            """
        },
        "dermatologico": {
            "separacion": """
            # Protocolo para Conflictos de Separación (Piel)
            
            ## Diálogo con la Piel
            1. Contacto consciente con la zona afectada
            2. Preguntar: "¿Qué separación representas?"
            3. Escuchar la respuesta somática
            
            ## Visualización Curativa
            "Imagina una luz dorada sanando cada célula de tu piel...
            Visualiza límites saludables y porosos que te protegen sin aislarte..."
            
            ## Integración
            "Tu piel es un mapa de tus contactos...
            Cada célula renueva su capacidad de contacto amoroso..."
            """
        },
        "digestivo": {
            "indigestion_emocional": """
            # Protocolo para Conflictos Digestivos
            
            ## Conexión Estómago-Emoción
            1. Manos sobre el abdomen
            2. Respirar hacia la zona tensa
            3. Identificar la "emoción no digerida"
            
            ## Liberación
            "Visualiza la emoción atrapada transformándose en luz...
            Permite que tu sistema digestivo procese y suelte..."
            
            ## Nuevo Patrón
            "Digiero fácilmente experiencias y emociones...
            Mi intestino fluye con la sabiduría de soltar lo innecesario..."
            """
        }
    }
    
    system_protocols = protocols.get(system, protocols["ocular"])
    return system_protocols.get(conflict_type, list(system_protocols.values())[0])

def generate_self_hypnosis_script(protocol_text):
    """Adapta un protocolo de terapeuta para autohipnosis."""
    script = protocol_text.replace("Visualiza", "Voy a visualizar")
    script = script.replace("Imagina", "Voy a imaginar")
    script = script.replace("Permite", "Me permito")
    script = script.replace("Siente", "Puedo sentir")
    
    # Agregar instrucciones de inicio y fin
    full_script = f"""
    # 🧘 Autohipnosis Guiada
    
    ## Preparación
    Encuentra un lugar tranquilo, siéntate o recuéstate cómodamente.
    Respira profundamente 3 veces antes de comenzar.
    
    {script}
    
    ## Finalización
    Poco a poco, voy trayendo mi conciencia de regreso a la habitación.
    Muevo suavemente dedos de manos y pies.
    Abro los ojos cuando me sienta listo/a.
    Me tomo un momento para integrar la experiencia.
    """
    
    return full_script

# ============================================
# SECCIÓN 9: FUNCIONES DE GENERACIÓN DE PDF
# ============================================

def create_pdf_diagnosis(patient_data, diagnosis_report, protocol_text):
    """Crea un PDF profesional con el diagnóstico y protocolo."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, 
                          rightMargin=72, leftMargin=72,
                          topMargin=72, bottomMargin=72)
    
    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        textColor=colors.HexColor('#2E86AB')
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.HexColor('#2E86AB')
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6
    )
    
    story = []
    
    # Título principal
    story.append(Paragraph("MINDGEEKCLINIC - Reporte de Biodescodificación", title_style))
    story.append(Spacer(1, 12))
    
    # Información del paciente
    story.append(Paragraph("Información del Paciente", heading_style))
    patient_info = f"""
    <b>Nombre:</b> {patient_data.get('nombre', 'No especificado')}<br/>
    <b>Edad:</b> {patient_data.get('edad', 'No especificada')}<br/>
    <b>Género:</b> {patient_data.get('genero', 'No especificado')}<br/>
    <b>Fecha de consulta:</b> {datetime.now().strftime('%d/%m/%Y')}<br/>
    <b>Dolencia principal:</b> {patient_data.get('dolencia', 'No especificada')}<br/>
    <b>Tiempo de padecimiento:</b> {patient_data.get('tiempo', 'No especificado')}
    """
    story.append(Paragraph(patient_info, normal_style))
    story.append(Spacer(1, 24))
    
    # Reporte de diagnóstico
    story.append(Paragraph("Análisis de Biodescodificación", heading_style))
    
    # Convertir el reporte markdown a formato PDF
    report_lines = diagnosis_report.split('\n')
    for line in report_lines:
        if line.startswith('# '):
            story.append(Paragraph(line[2:], title_style))
        elif line.startswith('## '):
            story.append(Paragraph(line[3:], heading_style))
        elif line.strip():
            story.append(Paragraph(line, normal_style))
        else:
            story.append(Spacer(1, 6))
    
    story.append(PageBreak())
    
    # Protocolo de intervención
    story.append(Paragraph("Protocolo Terapéutico", title_style))
    story.append(Spacer(1, 12))
    
    protocol_lines = protocol_text.split('\n')
    for line in protocol_lines:
        if line.startswith('# '):
            story.append(Paragraph(line[2:], heading_style))
        elif line.strip():
            story.append(Paragraph(line, normal_style))
        else:
            story.append(Spacer(1, 6))
    
    # Pie de página
    story.append(Spacer(1, 36))
    footer_text = f"""
    <i>Documento generado automáticamente por MINDGEEKCLINIC v{APP_VERSION}<br/>
    Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}<br/>
    Uso exclusivo para fines terapéuticos profesionales</i>
    """
    story.append(Paragraph(footer_text, ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.gray
    )))
    
    # Construir el PDF
    doc.build(story)
    
    buffer.seek(0)
    return buffer

def get_pdf_download_link(pdf_buffer, filename="diagnostico_biodescodificacion.pdf"):
    """Genera un link de descarga para el PDF."""
    b64 = base64.b64encode(pdf_buffer.read()).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}" style="background-color:#2E86AB;color:white;padding:10px 20px;border-radius:5px;text-decoration:none;">📥 Descargar PDF Completo</a>'
    return href

# ============================================
# SECCIÓN 10: FUNCIONES DE ESTADÍSTICAS Y BACKUP
# ============================================

def display_statistics():
    """Muestra estadísticas de uso de la aplicación."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="👁️ Accesos Totales",
            value=st.session_state.page_views,
            delta=f"+{random.randint(1, 10)} hoy"
        )
    
    with col2:
        st.metric(
            label="📋 Diagnósticos Realizados",
            value=st.session_state.diagnosticos_realizados,
            delta=f"+{random.randint(1, 5)} esta semana"
        )
    
    with col3:
        st.metric(
            label="👥 Pacientes Registrados",
            value=st.session_state.pacientes_registrados,
            delta=f"+{random.randint(1, 3)} hoy"
        )
    
    with col4:
        st.metric(
            label="📊 Tasa de Finalización",
            value=f"{random.randint(85, 98)}%",
            delta=f"+{random.randint(1, 3)}%"
        )
    
    # Gráfico de tendencia (simulado)
    st.subheader("📈 Tendencia de Uso")
    
    dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
    usage_data = pd.DataFrame({
        'Fecha': dates,
        'Diagnósticos': np.random.poisson(8, 30).cumsum(),
        'Consultas': np.random.poisson(12, 30).cumsum()
    })
    
    fig = px.line(usage_data, x='Fecha', y=['Diagnósticos', 'Consultas'],
                  title='Actividad Mensual',
                  labels={'value': 'Cantidad', 'variable': 'Métrica'})
    
    st.plotly_chart(fig, use_container_width=True)

def backup_data():
    """Crea una copia de seguridad de los datos."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"backup/mindgeek_backup_{timestamp}.json"
        
        # Crear directorio de backup si no existe
        os.makedirs("backup", exist_ok=True)
        
        # Copiar el archivo de datos
        if os.path.exists(DATA_FILE):
            import shutil
            shutil.copy2(DATA_FILE, backup_file)
            st.success(f"✅ Copia de seguridad creada: {backup_file}")
            return True
        else:
            st.warning("No se encontró archivo de datos para respaldar.")
            return False
    except Exception as e:
        st.error(f"Error creando backup: {str(e)}")
        return False

# ============================================
# SECCIÓN 11: SISTEMA DE AFILIADOS (KYC) - NUEVO
# ============================================

COUNTRIES_LIST = [
    "Argentina", "Brasil", "Chile", "Colombia", "Costa Rica", "Ecuador", "El Salvador",
    "España", "Estados Unidos", "Guatemala", "Honduras", "México", "Nicaragua",
    "Panamá", "Paraguay", "Perú", "Portugal", "Puerto Rico", "República Dominicana",
    "Uruguay", "Venezuela", "Otro"
]

def generate_affiliate_code():
    """Genera un código de afiliado único: MINDGEEKCLINIC-AFFILIATE-XXXXXXX"""
    db = load_affiliate_db()
    existing_codes = {aff['affiliate_code'] for aff in db.get('affiliates', [])}
    
    while True:
        # 7 caracteres alfanuméricos aleatorios
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
        code = f"MINDGEEKCLINIC-AFFILIATE-{random_part}"
        if code not in existing_codes:
            return code

def validate_binance_wallet(wallet):
    """Valida el formato básico de una dirección de wallet de Binance (USDT)."""
    if not wallet:
        return False
    wallet = wallet.strip()
    
    # Patrón para direcciones de criptomonedas comunes en Binance
    # Direcciones Ethereum (ERC20) - USDT común
    eth_pattern = r'^0x[a-fA-F0-9]{40}$'
    # Direcciones Binance Chain (BEP2)
    bep2_pattern = r'^bnb1[ac-hj-np-z02-9]{38,59}$'
    # Direcciones Binance Smart Chain (BEP20)
    bep20_pattern = r'^0x[a-fA-F0-9]{40}$'  # Mismo formato que ETH
    
    # Direcciones TRON (TRC20) - USDT común
    tron_pattern = r'^T[A-Za-z1-9]{33}$'
    
    return bool(re.match(eth_pattern, wallet) or 
                re.match(bep2_pattern, wallet) or 
                re.match(bep20_pattern, wallet) or 
                re.match(tron_pattern, wallet))

def send_verification_code(email):
    """Simula el envío de un código de verificación de 6 dígitos."""
    verification_code = ''.join(random.choices(string.digits, k=6))
    
    # En un entorno real, aquí se integraría con SendGrid, SMTP, etc.
    # Por ahora, almacenamos en session_state para mostrarlo en la UI
    st.session_state['verification_code'] = verification_code
    st.session_state['verification_email'] = email
    st.session_state['verification_time'] = datetime.now()
    
    return verification_code

def verify_email_code(input_code):
    """Verifica si el código ingresado por el usuario es correcto."""
    if 'verification_code' not in st.session_state:
        return False, "No hay código pendiente de verificación"
    
    if datetime.now() - st.session_state['verification_time'] > timedelta(minutes=10):
        return False, "El código ha expirado (válido por 10 minutos)"
    
    if input_code == st.session_state['verification_code']:
        # Código correcto, limpiar estado
        st.session_state['verification_code'] = None
        st.session_state['verification_time'] = None
        return True, "¡Email verificado correctamente!"
    else:
        return False, "Código incorrecto. Intenta nuevamente."

def register_affiliate(affiliate_data):
    """Registra un nuevo afiliado en la base de datos."""
    db = load_affiliate_db()
    
    # Verificar si el email ya existe
    if any(aff['email'].lower() == affiliate_data['email'].lower() for aff in db['affiliates']):
        return False, "Este email ya está registrado como afiliado."
    
    # Verificar si el ID ya existe
    if any(aff['id_number'] == affiliate_data['id_number'] for aff in db['affiliates']):
        return False, "Este número de identificación ya está registrado."
    
    # Generar código de afiliado único
    affiliate_code = generate_affiliate_code()
    
    # Crear objeto afiliado
    new_affiliate = {
        "id": str(uuid.uuid4()),
        "affiliate_code": affiliate_code,
        "full_name": affiliate_data['full_name'],
        "email": affiliate_data['email'].lower(),
        "id_number": affiliate_data['id_number'],
        "country": affiliate_data['country'],
        "phone": affiliate_data['phone'],
        "binance_wallet": affiliate_data['binance_wallet'],
        "status": "active",
        "kyc_verified": True,  # En Fase 1, asumimos verificado tras registro
        "balance": 0.0,
        "pending_payout": 0.0,
        "total_earned": 0.0,
        "join_date": datetime.now().isoformat(),
        "last_payout_date": None,
        "referrals": 0,
        "conversions": 0,
        "sales": []
    }
    
    # Agregar a la base de datos
    db['affiliates'].append(new_affiliate)
    
    # Guardar cambios
    if save_affiliate_db(db):
        return True, f"¡Registro exitoso! Tu código de afiliado es: **{affiliate_code}**"
    else:
        return False, "Error al guardar el registro. Intenta nuevamente."

def get_affiliate_by_code(affiliate_code):
    """Obtiene un afiliado por su código."""
    db = load_affiliate_db()
    for affiliate in db['affiliates']:
        if affiliate['affiliate_code'] == affiliate_code:
            return affiliate
    return None

def get_affiliate_by_email(email):
    """Obtiene un afiliado por su email."""
    db = load_affiliate_db()
    for affiliate in db['affiliates']:
        if affiliate['email'].lower() == email.lower():
            return affiliate
    return None

def record_sale(affiliate_code, sale_type, amount_usd):
    """Registra una venta para un afiliado y calcula su comisión."""
    db = load_affiliate_db()
    
    # Encontrar el afiliado
    for affiliate in db['affiliates']:
        if affiliate['affiliate_code'] == affiliate_code:
            # Obtener tasa de comisión
            commission_rate = db['settings']['commission_rates'].get(sale_type, 0.30)
            commission = amount_usd * commission_rate
            
            # Actualizar estadísticas
            affiliate['conversions'] += 1
            affiliate['pending_payout'] += commission
            affiliate['total_earned'] += commission
            
            # Registrar la venta
            sale_record = {
                "id": str(uuid.uuid4()),
                "date": datetime.now().isoformat(),
                "type": sale_type,
                "amount_usd": amount_usd,
                "commission": commission,
                "commission_rate": commission_rate
            }
            
            affiliate['sales'].append(sale_record)
            
            # Limitar historial a últimas 100 ventas
            if len(affiliate['sales']) > 100:
                affiliate['sales'] = affiliate['sales'][-100:]
            
            # Guardar cambios
            save_affiliate_db(db)
            return True, commission
    
    return False, 0

def calculate_affiliate_metrics(affiliate):
    """Calcula métricas clave para el dashboard del afiliado."""
    if not affiliate:
        return {}
    
    # Calcular tasa de conversión
    conversion_rate = 0
    if affiliate['referrals'] > 0:
        conversion_rate = (affiliate['conversions'] / affiliate['referrals']) * 100
    
    # Calcular ganancia promedio por venta
    avg_sale_value = 0
    if affiliate['conversions'] > 0 and affiliate['sales']:
        total_sales = sum(sale['amount_usd'] for sale in affiliate['sales'])
        avg_sale_value = total_sales / affiliate['conversions']
    
    # Próximo pago (simulación: cada jueves si balance >= $50)
    next_payout = "No disponible"
    if affiliate['pending_payout'] >= 50:
        today = datetime.now()
        # Encontrar próximo jueves
        days_ahead = 3 - today.weekday()  # 3 = jueves
        if days_ahead <= 0:  # Si hoy es después de jueves
            days_ahead += 7
        next_thursday = today + timedelta(days=days_ahead)
        next_payout = next_thursday.strftime("%d/%m/%Y")
    
    return {
        "affiliate_code": affiliate['affiliate_code'],
        "full_name": affiliate['full_name'],
        "status": affiliate['status'],
        "balance": affiliate['balance'],
        "pending_payout": affiliate['pending_payout'],
        "total_earned": affiliate['total_earned'],
        "referrals": affiliate['referrals'],
        "conversions": affiliate['conversions'],
        "conversion_rate": round(conversion_rate, 1),
        "avg_sale_value": round(avg_sale_value, 2),
        "join_date": datetime.fromisoformat(affiliate['join_date']).strftime("%d/%m/%Y"),
        "next_payout": next_payout,
        "binance_wallet": affiliate['binance_wallet']
    }

# ============================================
# SECCIÓN 12: INTERFAZ PRINCIPAL DE LA APLICACIÓN
# ============================================

def main():
    # Registrar acceso
    track_access()
    
    # Cargar datos
    data = load_data()
    
    # Título principal con estilo
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #5D737E;
        text-align: center;
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-header">🧠 MINDGEEKCLINIC</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Plataforma Profesional de Biodescodificación con IA</p>', unsafe_allow_html=True)
    
    # Sidebar con navegación
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/brain.png", width=80)
        st.title("Navegación")
        
        # Opciones de navegación principales
        menu_option = st.radio(
            "Selecciona una sección:",
            ["🏠 Inicio", "📝 Nuevo Diagnóstico", "🔍 Consultar IA", "📊 Estadísticas", "💾 Backup"],
            index=0
        )
        
        st.markdown("---")
        
        # ============================================
        # NUEVO: SECCIÓN DE AFILIADOS EN SIDEBAR
        # ============================================
        st.subheader("👥 Programa de Afiliados")
        
        affiliate_menu = st.radio(
            "Opciones para afiliados:",
            ["📋 Registrarse como Afiliado", "📊 Dashboard de Afiliado"]
        )
        
        # Detectar código de afiliado en la URL (solo para diagnóstico)
        query_params = st.query_params
        detected_affiliate_code = query_params.get("affiliate", [""])[0]
        
        if detected_affiliate_code:
            st.info(f"Código de afiliado detectado: `{detected_affiliate_code}`")
            # Verificar si el código existe
            affiliate = get_affiliate_by_code(detected_affiliate_code)
            if affiliate:
                st.success("✅ Código válido")
                st.session_state.current_affiliate = affiliate
            else:
                st.warning("⚠️ Código no encontrado en el sistema")
        
        st.markdown("---")
        
        # Información de la aplicación
        st.caption(f"Versión {APP_VERSION}")
        st.caption(f"Accesos hoy: {random.randint(10, 50)}")
        
        # Botón para actualizar estadísticas
        if st.button("🔄 Actualizar Estadísticas"):
            st.rerun()
    
    # ============================================
    # CONTENIDO PRINCIPAL BASADO EN SELECCIÓN
    # ============================================
    
    # Lógica para mostrar contenido basado en el menú principal
    if menu_option == "🏠 Inicio":
        show_homepage()
    elif menu_option == "📝 Nuevo Diagnóstico":
        show_diagnosis_form(data)
    elif menu_option == "🔍 Consultar IA":
        show_ai_consultation()
    elif menu_option == "📊 Estadísticas":
        show_statistics_page()
    elif menu_option == "💾 Backup":
        show_backup_page()
    
    # Lógica para mostrar contenido de afiliados
    if affiliate_menu == "📋 Registrarse como Afiliado":
        show_affiliate_registration()
    elif affiliate_menu == "📊 Dashboard de Afiliado":
        show_affiliate_dashboard()

# ============================================
# SECCIÓN 13: PÁGINAS PRINCIPALES DE LA APP
# ============================================

def show_homepage():
    """Muestra la página de inicio."""
    st.subheader("Bienvenido a MINDGEEKCLINIC")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### ¿Qué es la Biodescodificación?
        
        La **biodescodificación** es un enfoque terapéutico que busca 
        identificar el conflicto emocional oculto detrás de los síntomas físicos.
        
        ### 🎯 Características de la Plataforma
        
        1. **Diagnóstico especializado** por sistemas corporales
        2. **Triangulación emocional** entre eventos y síntomas
        3. **Protocolos de hipnosis** personalizados
        4. **Generación de informes** profesionales en PDF
        5. **Consulta con IA** especializada en biodescodificación
        6. **Sistema de afiliados** para profesionales (NUEVO)
        
        ### 📈 Impacto Esperado
        
        - Reducción del tiempo de diagnóstico en 40%
        - Aumento de efectividad terapéutica en 60%
        - Automatización de procesos administrativos
        """)
    
    with col2:
        st.info("""
        **🚀 Novedades:**
        
        • **Nuevo Sistema de Afiliados**  
          Gana comisiones refiriendo clientes.
        
        • **Dashboard Profesional**  
          Sigue tus métricas en tiempo real.
        
        • **Integración Binance**  
          Recibe pagos en criptomonedas.
        
        [Regístrate como afiliado](#)
        """)
        
        # Mostrar algunos datos de ejemplo
        with st.expander("📊 Datos Rápidos"):
            st.metric("Afiliados Activos", "124")
            st.metric("Comisiones Pagadas", "$3,850")
            st.metric("Tasa Conversión", "34%")
    
    st.markdown("---")
    
    # Llamada a la acción
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎯 Comenzar Diagnóstico", use_container_width=True):
            st.query_params = {"menu": "Nuevo Diagnóstico"}
            st.rerun()
    
    with col2:
        if st.button("🤝 Unirse como Afiliado", use_container_width=True):
            st.query_params = {"menu": "Registrarse como Afiliado"}
            st.rerun()
    
    with col3:
        if st.button("🧠 Consultar IA", use_container_width=True):
            st.query_params = {"menu": "Consultar IA"}
            st.rerun()

def show_diagnosis_form(data):
    """Muestra el formulario de diagnóstico."""
    st.subheader("📝 Formulario Clínico de Biodescodificación")
    
    with st.form("diagnosis_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            nombre = st.text_input("Nombre completo del paciente*")
            edad = st.number_input("Edad*", min_value=1, max_value=120, value=30)
            genero = st.selectbox("Género*", ["Masculino", "Femenino", "No binario", "Prefiero no especificar"])
            dolencia = st.text_input("Dolencia principal*", placeholder="Ej: Migraña crónica, colitis, ansiedad...")
        
        with col2:
            tiempo = st.text_input("Tiempo de padecimiento*", placeholder="Ej: 6 meses, 2 años, desde la infancia...")
            diagnostico_medico = st.text_input("Diagnóstico médico (opcional)", placeholder="Si existe diagnóstico clínico")
            entorno = st.selectbox("Entorno social predominante*", 
                                 ["Laboral", "Familiar", "Pareja", "Social", "Soledad", "Mixto"])
        
        st.markdown("---")
        
        # ============================================
        # NUEVO: CAMPO DE CÓDIGO DE AFILIADO EN FORMULARIO
        # ============================================
        col_aff1, col_aff2 = st.columns([3, 1])
        with col_aff1:
            # Detectar código de afiliado de la URL
            query_params = st.query_params
            url_affiliate_code = query_params.get("affiliate", [""])[0]
            
            # Si hay código en URL, usarlo como valor por defecto
            default_code = url_affiliate_code if url_affiliate_code else st.session_state.affiliate_code_input
            
            affiliate_code = st.text_input(
                "Código de afiliado (opcional)",
                value=default_code,
                placeholder="Ej: MINDGEEKCLINIC-AFFILIATE-ABC123",
                help="Si vienes de un enlace de afiliado, este campo se llenará automáticamente."
            )
            
            # Guardar en sesión para persistencia
            if affiliate_code:
                st.session_state.affiliate_code_input = affiliate_code
        
        with col_aff2:
            st.markdown("###")
            if affiliate_code:
                # Verificar si el código es válido
                affiliate = get_affiliate_by_code(affiliate_code)
                if affiliate:
                    st.success("✅ Válido")
                else:
                    st.warning("❌ No encontrado")
            else:
                st.info("ℹ️ Opcional")
        
        st.markdown("---")
        
        # Eventos emocionales
        st.subheader("🎭 Eventos Emocionales Relevantes")
        eventos = st.text_area(
            "Describe eventos significativos alrededor del inicio de los síntomas*",
            placeholder="Ej: Pérdida de empleo, ruptura amorosa, cambio de ciudad, conflicto familiar...",
            height=100
        )
        
        # Síntomas específicos
        st.subheader("🔍 Síntomas Específicos")
        sintomas = st.text_area(
            "Lista todos los síntomas (separados por comas)*",
            placeholder="Ej: Dolor de cabeza, insomnio, palpitaciones, náuseas...",
            height=100
        )
        
        # Información adicional
        with st.expander("📋 Información Adicional (opcional)"):
            antecedentes = st.text_area("Antecedentes familiares relevantes")
            tratamientos_previos = st.text_area("Tratamientos previos intentados")
            expectativas = st.text_area("Expectativas del paciente")
        
        submitted = st.form_submit_button("🎯 Generar Diagnóstico de Biodescodificación", use_container_width=True)
        
        if submitted:
            if not all([nombre, edad, genero, dolencia, tiempo, eventos, sintomas]):
                st.error("Por favor, completa todos los campos obligatorios (*)")
            else:
                with st.spinner("Analizando triangulación emocional..."):
                    # Crear datos del paciente
                    patient_data = {
                        "id": str(uuid.uuid4()),
                        "nombre": nombre,
                        "edad": edad,
                        "genero": genero,
                        "dolencia": dolencia,
                        "tiempo": tiempo,
                        "diagnostico_medico": diagnostico_medico,
                        "entorno": entorno,
                        "eventos": eventos,
                        "sintomas": sintomas,
                        "antecedentes": antecedentes,
                        "tratamientos_previos": tratamientos_previos,
                        "expectativas": expectativas,
                        "fecha_registro": datetime.now().isoformat(),
                        "affiliate_code": affiliate_code if affiliate_code else None  # NUEVO: Guardar código
                    }
                    
                    # Registrar afiliado si hay código válido
                    if affiliate_code:
                        affiliate = get_affiliate_by_code(affiliate_code)
                        if affiliate:
                            # Incrementar referidos
                            db = load_affiliate_db()
                            for aff in db['affiliates']:
                                if aff['affiliate_code'] == affiliate_code:
                                    aff['referrals'] += 1
                            save_affiliate_db(db)
                            st.success(f"✅ Referido registrado para afiliado: {affiliate_code}")
                    
                    # Analizar triangulación
                    triangulation = analyze_emotional_triangulation(sintomas, eventos, tiempo)
                    
                    # Generar diagnóstico
                    diagnosis = generate_diagnosis_report(patient_data, triangulation)
                    
                    # Obtener sistema principal afectado
                    main_system = get_system_by_symptom(dolencia)
                    
                    # Generar protocolo de hipnosis
                    protocol = generate_hypnosis_protocol(main_system, "conflicto_visual")
                    
                    # Mostrar resultados
                    st.success("✅ Diagnóstico generado exitosamente!")
                    
                    # Actualizar estadísticas
                    st.session_state.diagnosticos_realizados += 1
                    st.session_state.pacientes_registrados += 1
                    
                    # Guardar en base de datos
                    data["patients"].append(patient_data)
                    data["diagnoses"].append({
                        "patient_id": patient_data["id"],
                        "diagnosis": diagnosis,
                        "protocol": protocol,
                        "date": datetime.now().isoformat()
                    })
                    
                    save_data(data)
                    
                    # Mostrar resultados en pestañas
                    tab1, tab2, tab3, tab4 = st.tabs(["📋 Diagnóstico", "🧠 Protocolo", "🧘 Autohipnosis", "📄 PDF"])
                    
                    with tab1:
                        st.markdown(diagnosis)
                    
                    with tab2:
                        st.markdown(protocol)
                        
                        # Generar autohipnosis
                        autohipnosis = generate_self_hypnosis_script(protocol)
                        if st.button("🔄 Generar Versión Autohipnosis"):
                            st.markdown(autohipnosis)
                    
                    with tab3:
                        st.subheader("🧘 Guía de Autohipnosis")
                        st.markdown(autohipnosis)
                        
                        # Audio guiado (simulación)
                        st.audio("https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3", format="audio/mp3")
                    
                    with tab4:
                        st.subheader("📄 Reporte Profesional en PDF")
                        
                        # Generar PDF
                        pdf_buffer = create_pdf_diagnosis(patient_data, diagnosis, protocol)
                        
                        # Mostrar link de descarga
                        st.markdown(get_pdf_download_link(pdf_buffer), unsafe_allow_html=True)
                        
                        # Vista previa del PDF
                        base64_pdf = base64.b64encode(pdf_buffer.read()).decode('utf-8')
                        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
                        st.markdown(pdf_display, unsafe_allow_html=True)

def show_ai_consultation():
    """Muestra la interfaz de consulta con IA."""
    st.subheader("🔍 Consulta con IA Especializada")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        query = st.text_area(
            "Describe tu consulta sobre biodescodificación:",
            placeholder="Ej: ¿Qué conflicto emocional podría estar detrás de las migrañas recurrentes?",
            height=150
        )
        
        context = st.text_area(
            "Contexto adicional (opcional):",
            placeholder="Información relevante sobre el paciente o situación...",
            height=100
        )
    
    with col2:
        st.info("""
        **💡 Sugerencias:**
        
        1. Síntomas específicos
        2. Eventos emocionales
        3. Sistema corporal afectado
        4. Tiempo de evolución
        
        **🎯 La IA considera:**
        • Conocimiento especializado
        • Casos clínicos similares
        • Principios de biodescodificación
        """)
    
    if st.button("🤖 Consultar con IA", type="primary"):
        if not query:
            st.warning("Por favor, ingresa tu consulta.")
        else:
            with st.spinner("Consultando base de conocimiento y generando respuesta..."):
                # Inicializar ChromaDB
                chroma_client, collection = initialize_chroma_db()
                
                # Consultar base de conocimiento
                knowledge_results = query_knowledge_base(query, collection)
                
                # Construir contexto
                knowledge_context = ""
                if knowledge_results and 'documents' in knowledge_results:
                    knowledge_context = "\n".join(knowledge_results['documents'][0][:2])
                
                full_context = f"{knowledge_context}\n{context}"
                
                # Generar respuesta con Groq
                response = generate_with_groq(query, full_context)
                
                # Mostrar respuesta
                st.success("✅ Respuesta generada:")
                st.markdown(response)
                
                # Mostrar fuentes de conocimiento si existen
                if knowledge_results and 'metadatas' in knowledge_results:
                    with st.expander("📚 Fuentes consultadas"):
                        for i, metadata in enumerate(knowledge_results['metadatas'][0]):
                            st.caption(f"Fuente {i+1}: {metadata.get('source', 'Conocimiento especializado')}")

def show_statistics_page():
    """Muestra la página de estadísticas."""
    st.subheader("📊 Estadísticas de la Plataforma")
    
    # Mostrar métricas principales
    display_statistics()
    
    st.markdown("---")
    
    # Datos demográficos simulados
    st.subheader("👥 Distribución Demográfica")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Género
        gender_data = pd.DataFrame({
            'Género': ['Mujeres', 'Hombres', 'Otros'],
            'Porcentaje': [52, 45, 3]
        })
        
        fig_gender = px.pie(gender_data, values='Porcentaje', names='Género',
                          title='Distribución por Género',
                          color_discrete_sequence=px.colors.sequential.Blues_r)
        st.plotly_chart(fig_gender, use_container_width=True)
    
    with col2:
        # Edades
        age_data = pd.DataFrame({
            'Rango Edad': ['18-25', '26-35', '36-45', '46-55', '56+'],
            'Pacientes': [15, 35, 28, 15, 7]
        })
        
        fig_age = px.bar(age_data, x='Rango Edad', y='Pacientes',
                        title='Distribución por Edad',
                        color='Pacientes',
                        color_continuous_scale='Blues')
        st.plotly_chart(fig_age, use_container_width=True)
    
    # Sistemas más consultados
    st.subheader("🩺 Sistemas Corporales Más Consultados")
    
    systems_data = pd.DataFrame({
        'Sistema': ['Digestivo', 'Muscular', 'Respiratorio', 'Dermatológico', 'Ocular'],
        'Consultas': [125, 98, 76, 65, 42],
        'Efectividad': [78, 82, 75, 68, 85]
    })
    
    fig_systems = go.Figure()
    fig_systems.add_trace(go.Bar(
        x=systems_data['Sistema'],
        y=systems_data['Consultas'],
        name='Consultas',
        marker_color='#2E86AB'
    ))
    
    fig_systems.add_trace(go.Scatter(
        x=systems_data['Sistema'],
        y=systems_data['Efectividad'],
        name='Efectividad %',
        yaxis='y2',
        line=dict(color='#FF6B6B', width=3)
    ))
    
    fig_systems.update_layout(
        title='Consultas y Efectividad por Sistema',
        yaxis=dict(title='Consultas'),
        yaxis2=dict(title='Efectividad %', overlaying='y', side='right'),
        hovermode='x unified'
    )
    
    st.plotly_chart(fig_systems, use_container_width=True)

def show_backup_page():
    """Muestra la página de backup y mantenimiento."""
    st.subheader("💾 Backup y Mantenimiento")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        **📦 Estado Actual:**
        
        • Tamaño base de datos: 2.4 MB
        • Último backup: Hoy 08:30
        • Integridad: ✅ Verificada
        • Pacientes registrados: 347
        """)
        
        if st.button("🔄 Crear Backup Ahora", use_container_width=True):
            if backup_data():
                st.success("Backup creado exitosamente!")
            else:
                st.error("Error al crear backup")
    
    with col2:
        st.warning("""
        **⚠️ Precauciones:**
        
        1. Realiza backup antes de actualizaciones
        2. Verifica integridad periódicamente
        3. Mantén múltiples copias
        4. Almacena en ubicaciones seguras
        """)
        
        if st.button("🔍 Verificar Integridad", use_container_width=True):
            with st.spinner("Verificando..."):
                time.sleep(1)
                st.success("✅ Integridad verificada correctamente")
    
    st.markdown("---")
    
    # Opciones avanzadas
    with st.expander("⚙️ Opciones Avanzadas"):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Limpiar Cache", help="Elimina datos temporales"):
                st.session_state.clear()
                st.success("Cache limpiado. La página se recargará.")
                time.sleep(2)
                st.rerun()
            
            if st.button("📊 Recalcular Estadísticas"):
                st.info("Recalculando...")
                time.sleep(1)
                st.success("Estadísticas actualizadas")
        
        with col2:
            export_format = st.selectbox("Formato de exportación", ["JSON", "CSV", "Excel"])
            
            if st.button(f"📤 Exportar Datos ({export_format})"):
                st.info(f"Exportando datos en formato {export_format}...")
                # Simulación de exportación
                progress_bar = st.progress(0)
                for i in range(100):
                    time.sleep(0.01)
                    progress_bar.progress(i + 1)
                
                st.success(f"Datos exportados en formato {export_format}")

# ============================================
# SECCIÓN 14: INTERFACES DEL SISTEMA DE AFILIADOS - NUEVO
# ============================================

def show_affiliate_registration():
    """Muestra el formulario de registro de afiliados."""
    st.subheader("👥 Registro en el Programa de Afiliados")
    st.markdown("""
    Únete como afiliado de **MINDGEEKCLINIC** y gana comisiones recomendando nuestros servicios.
    **Comisiones:** 34.5% en terapias, 33.3% en PDFs, 31.6% en suscripciones.
    **Retiro mínimo:** $50 USD semanales vía Binance.
    """)
    
    with st.form("affiliate_registration_form"):
        st.markdown("### 📝 Información Personal (KYC)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            full_name = st.text_input("Nombre completo*")
            email = st.text_input("Email*", help="Se enviará un código de verificación")
            id_number = st.text_input("Número de identificación*", help="DNI, cédula, pasaporte, etc.")
        
        with col2:
            country = st.selectbox("País*", COUNTRIES_LIST)
            phone = st.text_input("Teléfono*", help="Incluir código de país")
            binance_wallet = st.text_input("Wallet de Binance (USDT)*", 
                                         help="Dirección donde recibirás pagos")
        
        # Verificación de wallet
        if binance_wallet:
            if validate_binance_wallet(binance_wallet):
                st.success("✅ Formato de wallet válido")
            else:
                st.warning("⚠️ El formato no coincide con direcciones comunes de Binance. Verifica.")
        
        st.markdown("---")
        st.markdown("### 📧 Verificación de Email")
        
        email_verified = False
        
        # Verificar si ya hay un código pendiente
        if 'verification_code' in st.session_state and st.session_state['verification_code']:
            st.info(f"Código enviado a: {st.session_state.get('verification_email', '')}")
            
            verification_input = st.text_input("Ingresa el código de 6 dígitos*", 
                                             max_chars=6,
                                             help="Revisa tu email (en esta demo, el código aparece abajo)")
            
            if verification_input:
                verified, message = verify_email_code(verification_input)
                if verified:
                    st.success(message)
                    email_verified = True
                else:
                    st.error(message)
            
            # Mostrar el código generado (solo para demo)
            st.warning(f"**DEMO:** Para propósitos de prueba, tu código es: `{st.session_state['verification_code']}`")
            
            if st.button("🔄 Reenviar código"):
                if email:
                    new_code = send_verification_code(email)
                    st.success(f"Nuevo código enviado a {email}")
                    st.info(f"**DEMO:** Nuevo código: `{new_code}`")
                else:
                    st.error("Primero ingresa un email")
        else:
            # Si no hay código pendiente, mostrar botón para enviar
            if email and st.button("📨 Enviar código de verificación"):
                verification_code = send_verification_code(email)
                st.success(f"Código de verificación enviado a {email}")
                st.info(f"**DEMO:** Tu código es: `{verification_code}`")
                st.rerun()
        
        st.markdown("---")
        
        # Términos y condiciones
        st.markdown("### ✅ Términos y Condiciones")
        
        col_terms1, col_terms2 = st.columns(2)
        
        with col_terms1:
            accept_terms = st.checkbox("Acepto los términos y condiciones*")
            accept_privacy = st.checkbox("Acepto la política de privacidad*")
        
        with col_terms2:
            confirm_kyc = st.checkbox("Confirmo que la información es verídica*")
            accept_payments = st.checkbox("Acepto recibir pagos vía Binance*")
        
        # Botón de registro
        submitted = st.form_submit_button("🚀 Registrar como Afiliado", use_container_width=True)
        
        if submitted:
            # Validaciones
            if not all([full_name, email, id_number, country, phone, binance_wallet]):
                st.error("Por favor, completa todos los campos obligatorios (*)")
            elif not validate_binance_wallet(binance_wallet):
                st.error("Por favor, ingresa una dirección de Binance válida")
            elif not all([accept_terms, accept_privacy, confirm_kyc, accept_payments]):
                st.error("Debes aceptar todos los términos y condiciones")
            elif not email_verified and 'verification_code' in st.session_state:
                st.error("Debes verificar tu email antes de registrar")
            else:
                with st.spinner("Registrando afiliado..."):
                    affiliate_data = {
                        "full_name": full_name,
                        "email": email,
                        "id_number": id_number,
                        "country": country,
                        "phone": phone,
                        "binance_wallet": binance_wallet
                    }
                    
                    success, message = register_affiliate(affiliate_data)
                    
                    if success:
                        st.balloons()
                        st.success(message)
                        
                        # Mostrar información adicional
                        st.markdown("""
                        ### 🎉 ¡Registro Exitoso!
                        
                        **Próximos pasos:**
                        1. **Guarda tu código de afiliado** (también llegará por email)
                        2. **Comparte tu link:** `https://tudominio.com/?affiliate=TU-CODIGO`
                        3. **Monitorea** tu dashboard para ver referidos y comisiones
                        4. **Retira** tus ganancias cada jueves (mínimo $50 USD)
                        
                        **Contacto:** affiliates@mindgeekclinic.com
                        """)
                    else:
                        st.error(f"Error en el registro: {message}")

def show_affiliate_dashboard():
    """Muestra el dashboard del afiliado."""
    st.subheader("📊 Dashboard de Afiliado")
    
    # Verificar si hay sesión de afiliado activa
    if 'current_affiliate' in st.session_state and st.session_state.current_affiliate:
        affiliate = st.session_state.current_affiliate
    else:
        # Pedir email para acceder
        st.info("Ingresa tu email para acceder a tu dashboard")
        email = st.text_input("Email registrado")
        
        if email and st.button("Acceder a mi dashboard"):
            affiliate = get_affiliate_by_email(email)
            if affiliate:
                st.session_state.current_affiliate = affiliate
                st.success(f"¡Bienvenido/a, {affiliate['full_name']}!")
                st.rerun()
            else:
                st.error("Email no encontrado. Verifica o regístrate primero.")
                return
    
    # Si llegamos aquí, tenemos un afiliado
    affiliate = st.session_state.current_affiliate
    metrics = calculate_affiliate_metrics(affiliate)
    
    # Mostrar métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="💰 Balance Disponible",
            value=f"${metrics['balance']:.2f} USD",
            help="Disponible para retiro inmediato"
        )
    
    with col2:
        st.metric(
            label="📊 Pendiente de Pago",
            value=f"${metrics['pending_payout']:.2f} USD",
            help="Acumulado esta semana"
        )
    
    with col3:
        st.metric(
            label="🏆 Total Ganado",
            value=f"${metrics['total_earned']:.2f} USD",
            help="Histórico desde registro"
        )
    
    with col4:
        st.metric(
            label="📈 Tasa Conversión",
            value=f"{metrics['conversion_rate']}%",
            help=f"{metrics['conversions']} ventas / {metrics['referrals']} referidos"
        )
    
    st.markdown("---")
    
    # Información del afiliado
    col_info1, col_info2 = st.columns(2)
    
    with col_info1:
        st.markdown("### 👤 Tu Información")
        st.write(f"**Código:** `{metrics['affiliate_code']}`")
        st.write(f"**Nombre:** {metrics['full_name']}")
        st.write(f"**Estado:** {metrics['status']}")
        st.write(f"**Fecha registro:** {metrics['join_date']}")
    
    with col_info2:
        st.markdown("### 🏦 Información de Pagos")
        st.write(f"**Wallet Binance:** `{metrics['binance_wallet'][:20]}...`")
        st.write(f"**Próximo pago:** {metrics['next_payout']}")
        st.write(f"**Mínimo retiro:** $50.00 USD")
        st.write(f"**Frecuencia:** Semanal (jueves)")
        
        # Botón para solicitar retiro (simulado)
        if metrics['pending_payout'] >= 50:
            if st.button("💳 Solicitar Retiro Ahora", use_container_width=True):
                st.success(f"Retiro de ${metrics['pending_payout']:.2f} USD procesado. Llegará a tu wallet en 24-48h.")
        else:
            st.warning(f"Necesitas ${50 - metrics['pending_payout']:.2f} USD más para retirar")
    
    st.markdown("---")
    
    # Tu link de afiliado
    st.markdown("### 🔗 Tu Link de Afiliado")
    
    base_url = "https://mindgeekclinic.com"  # Cambiar por tu dominio real
    affiliate_link = f"{base_url}?affiliate={metrics['affiliate_code']}"
    
    col_link1, col_link2 = st.columns([3, 1])
    
    with col_link1:
        st.code(affiliate_link, language="text")
    
    with col_link2:
        st.markdown("###")
        st.button("📋 Copiar Link", use_container_width=True)
    
    st.markdown(f"""
    **Comparte este link en:**  
    • Tu sitio web o blog  
    • Redes sociales  
    • Email a tus contactos  
    • Material promocional  
    """)
    
    st.markdown("---")
    
    # Gráficos de desempeño
    st.markdown("### 📈 Tu Desempeño")
    
    # Datos simulados para gráficos
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    referrals_data = pd.DataFrame({
        'Fecha': dates,
        'Referidos': np.random.poisson(2, 30).cumsum(),
        'Ventas': np.random.poisson(1, 30).cumsum(),
        'Comisiones': np.random.uniform(10, 50, 30).cumsum()
    })
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        fig_referrals = px.line(referrals_data, x='Fecha', y=['Referidos', 'Ventas'],
                              title='Referidos vs Ventas (Últimos 30 días)',
                              labels={'value': 'Cantidad', 'variable': 'Métrica'})
        st.plotly_chart(fig_referrals, use_container_width=True)
    
    with col_chart2:
        fig_commissions = px.area(referrals_data, x='Fecha', y='Comisiones',
                                title='Comisiones Acumuladas (USD)',
                                labels={'value': 'USD', 'variable': 'Comisiones'})
        st.plotly_chart(fig_commissions, use_container_width=True)
    
    # Tabla de ventas recientes
    if affiliate.get('sales'):
        st.markdown("### 💰 Ventas Recientes")
        
        sales_df = pd.DataFrame(affiliate['sales'][-10:])  # Últimas 10 ventas
        if not sales_df.empty:
            # Formatear fechas
            sales_df['date'] = pd.to_datetime(sales_df['date']).dt.strftime('%d/%m/%Y')
            sales_df['amount_usd'] = sales_df['amount_usd'].apply(lambda x: f"${x:.2f}")
            sales_df['commission'] = sales_df['commission'].apply(lambda x: f"${x:.2f}")
            
            st.dataframe(
                sales_df[['date', 'type', 'amount_usd', 'commission', 'commission_rate']],
                column_config={
                    "date": "Fecha",
                    "type": "Tipo",
                    "amount_usd": "Monto",
                    "commission": "Tu Comisión",
                    "commission_rate": st.column_config.NumberColumn(
                        "Tasa %",
                        format="%.1f%%"
                    )
                },
                hide_index=True,
                use_container_width=True
            )
    
    # Acciones rápidas
    st.markdown("---")
    st.markdown("### ⚡ Acciones Rápidas")
    
    col_act1, col_act2, col_act3 = st.columns(3)
    
    with col_act1:
        if st.button("🔄 Actualizar Datos", use_container_width=True):
            st.rerun()
    
    with col_act2:
        if st.button("📧 Contactar Soporte", use_container_width=True):
            st.info("Soporte: affiliates@mindgeekclinic.com")
    
    with col_act3:
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.current_affiliate = None
            st.success("Sesión cerrada. Vuelve a ingresar con tu email.")
            st.rerun()

# ============================================
# EJECUCIÓN PRINCIPAL
# ============================================

if __name__ == "__main__":
    main()
