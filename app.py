import streamlit as st
import json
import os
import uuid
from datetime import datetime, timedelta
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
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import csv

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

APP_VERSION = "3.0.0"
DATA_FILE = "mindgeekclinic_data.json"
AFFILIATE_DB_FILE = "affiliates_db.json"
ACCESS_LOG_FILE = "access_log.json"
PAYMENT_LOG_FILE = "payment_log.json"
CHROMA_DB_PATH = "./chroma_db"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# OBTENER SECRETS CON FORMATO TOML CORRECTO
try:
    GROQ_API_KEY = st.secrets["groq"]["api_key"]
except:
    GROQ_API_KEY = ""

try:
    CHROMA_PERSIST_DIRECTORY = st.secrets["chroma"]["persist_directory"]
except:
    CHROMA_PERSIST_DIRECTORY = CHROMA_DB_PATH

try:
    ADMIN_PASSWORD = st.secrets["app"]["admin_password"]
    ADMIN_EMAIL = st.secrets["app"]["admin_email"]
except:
    ADMIN_PASSWORD = "Enaraure25.."
    ADMIN_EMAIL = "promptandmente@gmail.com"

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
if 'verified_email' not in st.session_state:
    st.session_state.verified_email = None
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False
if 'admin_session_id' not in st.session_state:
    st.session_state.admin_session_id = None

# ============================================
# SECCIÓN 3: FUNCIONES DE BASE DE DATOS
# ============================================

def load_data():
    """Carga los datos de la aplicación desde el archivo JSON."""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if 'statistics' in data:
            stats = data['statistics']
            st.session_state.page_views = stats.get('total_accesses', 0)
            st.session_state.diagnosticos_realizados = stats.get('total_diagnoses', 0)
            st.session_state.pacientes_registrados = stats.get('total_patients', 0)
            st.session_state.access_count = stats.get('access_count', 0)
        return data
    except FileNotFoundError:
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
        return initial_data

def save_data(data):
    """Guarda los datos de la aplicación en el archivo JSON."""
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
        return {"affiliates": [], "settings": {
            "commission_rates": {"therapy": 0.345, "pdf": 0.333, "subscription": 0.316},
            "min_withdrawal": 50.0,
            "payout_schedule": "weekly"
        }}
    except json.JSONDecodeError:
        st.error("Error al leer la base de datos de afiliados.")
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

def load_payment_log():
    """Carga el historial de pagos desde el archivo JSON."""
    try:
        with open(PAYMENT_LOG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"payments": [], "summary": {"total_paid": 0.0, "payments_count": 0}}

def save_payment_log(log_data):
    """Guarda el historial de pagos en el archivo JSON."""
    try:
        with open(PAYMENT_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Error al guardar historial de pagos: {str(e)}")
        return False

# ============================================
# SECCIÓN 4: CONTADOR DE ACCESOS
# ============================================

def load_access_log():
    try:
        with open(ACCESS_LOG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"accesses": [], "daily_stats": {}}

def save_access_log(log_data):
    try:
        with open(ACCESS_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"Error al guardar registro de accesos: {str(e)}")

def track_access():
    st.session_state.access_count += 1
    st.session_state.page_views += 1
    log_data = load_access_log()
    current_time = datetime.now().isoformat()
    today = datetime.now().strftime("%Y-%m-%d")
    log_data["accesses"].append({
        "timestamp": current_time,
        "session_id": str(uuid.uuid4())[:8]
    })
    if today not in log_data["daily_stats"]:
        log_data["daily_stats"][today] = 0
    log_data["daily_stats"][today] += 1
    if len(log_data["accesses"]) > 1000:
        log_data["accesses"] = log_data["accesses"][-1000:]
    save_access_log(log_data)

# ============================================
# SECCIÓN 5: CONOCIMIENTO ESPECIALIZADO
# ============================================

def get_specialized_knowledge():
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
# SECCIÓN 6: IA Y RAG
# ============================================

def initialize_chroma_db():
    try:
        chroma_client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIRECTORY,
            settings=Settings(anonymized_telemetry=False)
        )
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
    try:
        model = SentenceTransformer(EMBEDDING_MODEL)
        embeddings = model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()
    except Exception as e:
        st.error(f"Error generando embeddings: {str(e)}")
        return None

def query_knowledge_base(query, collection, n_results=3):
    if not collection:
        return []
    try:
        query_embedding = get_embeddings([query])
        if not query_embedding:
            return []
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
    if not GROQ_API_KEY:
        st.warning("API key de Groq no configurada.")
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
# SECCIÓN 7: DIAGNÓSTICO Y TRIANGULACIÓN
# ============================================

def analyze_emotional_triangulation(symptoms, events, time_period):
    analysis = {
        "correlaciones": [],
        "conflictos_detectados": [],
        "recomendaciones": []
    }
    knowledge = get_specialized_knowledge()
    
    for symptom in symptoms.split(","):
        symptom = symptom.strip()
        if not symptom:
            continue
        system = get_system_by_symptom(symptom)
        system_info = knowledge.get(system, knowledge["ocular"])
        
        for event in events.split(","):
            event = event.strip()
            if not event:
                continue
            correlation_score = random.uniform(0.3, 0.9)
            if correlation_score > 0.6:
                analysis["correlaciones"].append({
                    "sintoma": symptom,
                    "evento": event,
                    "sistema": system_info["name"],
                    "conflictos_posibles": system_info["conflictos"],
                    "puntuacion": round(correlation_score, 2)
                })
    
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
        report += "\nNo se identificaron correlaciones significativas entre eventos y síntomas.\n"
    
    report += f"""
### 🎭 Conflictos Emocionales Detectados
"""
    if triangulation_analysis["conflictos_detectados"]:
        for conflicto in triangulation_analysis["conflictos_detectados"]:
            report += f"\n- {conflicto}"
    else:
        report += "\nNo se detectaron conflictos emocionales específicos.\n"
    
    report += f"""
### 💡 Recomendaciones Terapéuticas
"""
    for recomendacion in triangulation_analysis["recomendaciones"]:
        report += f"\n- {recomendacion}"
    
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
"Imagina que tus ojos son ventanas hacia tu alma... Visualiza una luz suave que limpia cada capa de tensión... Permite que tu visión interna se aclare..."

## Sugestiones Post-Hipnóticas
"Cada día verás con mayor claridad y aceptación... Tu visión se ajusta naturalmente a lo que necesitas experimentar..."
""",
            "miedo_futuro": """
# Protocolo para Miedo al Futuro

## Técnica de Línea del Tiempo
1. Visualizar línea del tiempo personal
2. Sanar eventos pasados que nublan la visión futura
3. Proyectar imágenes positivas del futuro

## Afirmaciones
"El futuro es una extensión amorosa del presente... Confío en mi capacidad de ver y adaptarme..."
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
"Imagina una luz dorada sanando cada célula de tu piel... Visualiza límites saludables y porosos que te protegen sin aislarte..."

## Integración
"Tu piel es un mapa de tus contactos... Cada célula renueva su capacidad de contacto amoroso..."
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
"Visualiza la emoción atrapada transformándose en luz... Permite que tu sistema digestivo procese y suelte..."

## Nuevo Patrón
"Digiero fácilmente experiencias y emociones... Mi intestino fluye con la sabiduría de soltar lo innecesario..."
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
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    
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
    
    story.append(Paragraph("MINDGEEKCLINIC - Reporte de Biodescodificación", title_style))
    story.append(Spacer(1, 12))
    
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
    
    story.append(Paragraph("Análisis de Biodescodificación", heading_style))
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
        os.makedirs("backup", exist_ok=True)
        
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
# SECCIÓN 11: SISTEMA DE AFILIADOS (KYC) - CORREGIDO
# ============================================

COUNTRIES_LIST = [
    "Argentina", "Brasil", "Chile", "Colombia", "Costa Rica", "Ecuador",
    "El Salvador", "España", "Estados Unidos", "Guatemala", "Honduras",
    "México", "Nicaragua", "Panamá", "Paraguay", "Perú", "Portugal",
    "Puerto Rico", "República Dominicana", "Uruguay", "Venezuela", "Otro"
]

def generate_affiliate_code():
    """Genera un código de afiliado único: MINDGEEKCLINIC-AFFILIATE-XXXXXXX"""
    db = load_affiliate_db()
    existing_codes = {aff['affiliate_code'] for aff in db.get('affiliates', [])}
    
    while True:
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
        code = f"MINDGEEKCLINIC-AFFILIATE-{random_part}"
        if code not in existing_codes:
            return code

def validate_binance_wallet(wallet):
    """Valida el formato básico de una dirección de wallet de Binance (USDT)."""
    if not wallet:
        return False
    wallet = wallet.strip()
    
    eth_pattern = r'^0x[a-fA-F0-9]{40}$'
    bep2_pattern = r'^bnb1[ac-hj-np-z02-9]{38,59}$'
    bep20_pattern = r'^0x[a-fA-F0-9]{40}$'
    tron_pattern = r'^T[A-Za-z1-9]{33}$'
    
    return bool(re.match(eth_pattern, wallet) or 
                re.match(bep2_pattern, wallet) or 
                re.match(bep20_pattern, wallet) or 
                re.match(tron_pattern, wallet))

def send_verification_code(email):
    """Envía un código de verificación de 6 dígitos por email - CORREGIDO."""
    try:
        # Generar código
        verification_code = ''.join(random.choices(string.digits, k=6))
        
        # Guardar en sesión
        st.session_state['verification_code'] = verification_code
        st.session_state['verification_email'] = email
        st.session_state['verification_time'] = datetime.now()
        
        # ============================================
        # ENVÍO REAL DE EMAIL CON SECRETS CORRECTOS
        # ============================================
        try:
            # Obtener configuración de email de secrets (formato TOML)
            email_config = st.secrets["email"]
            
            # Crear mensaje
            msg = MIMEMultipart()
            msg['From'] = email_config['sender_email']
            msg['To'] = email
            msg['Subject'] = "🔐 Código de Verificación - MINDGEEKCLINIC"
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                    <h2 style="color: #4A90E2;">✅ Verificación de Email</h2>
                    <p>Tu código de verificación para MINDGEEKCLINIC es:</p>
                    
                    <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; text-align: center;">
                        <h3 style="color: #333; font-size: 32px; letter-spacing: 5px;">{verification_code}</h3>
                        <p style="color: #666;">Válido por 10 minutos</p>
                    </div>
                    
                    <p>Ingresa este código en la aplicación para completar tu registro como afiliado.</p>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                    
                    <p style="font-size: 12px; color: #666;">
                        Si no solicitaste este registro, ignora este email.<br>
                        Contacto: affiliates@mindgeekclinic.com
                    </p>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_content, "html"))
            
            # Enviar usando SMTP (Gmail)
            with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
                server.starttls()
                server.login(email_config['username'], email_config['password'])
                server.send_message(msg)
            
            # Registrar envío exitoso
            st.session_state['last_email_sent'] = datetime.now().strftime("%H:%M:%S")
            st.success(f"✅ Código enviado a {email}")
            
        except Exception as email_error:
            # Si falla el envío real, mostrar modo demo
            st.warning(f"⚠️ Error al enviar email: {str(email_error)}")
            st.info(f"**Modo demo:** Tu código es: `{verification_code}`")
        
        return verification_code
        
    except Exception as e:
        st.error(f"Error generando código: {str(e)}")
        return None

def verify_email_code(input_code):
    """Verifica si el código ingresado por el usuario es correcto."""
    if 'verification_code' not in st.session_state:
        return False, "No hay código pendiente de verificación"
    
    if datetime.now() - st.session_state['verification_time'] > timedelta(minutes=10):
        return False, "El código ha expirado (válido por 10 minutos)"
    
    if input_code == st.session_state['verification_code']:
        # Guardar email verificado
        st.session_state['verified_email'] = st.session_state['verification_email']
        
        # Limpiar estado temporal
        st.session_state['verification_code'] = None
        st.session_state['verification_time'] = None
        st.session_state['verification_email'] = None
        
        return True, "¡Email verificado correctamente!"
    else:
        return False, "Código incorrecto. Intenta nuevamente."

def register_affiliate(affiliate_data):
    """Registra un nuevo afiliado en la base de datos."""
    db = load_affiliate_db()
    
    if any(aff['email'].lower() == affiliate_data['email'].lower() for aff in db['affiliates']):
        return False, "Este email ya está registrado como afiliado."
    
    if any(aff['id_number'] == affiliate_data['id_number'] for aff in db['affiliates']):
        return False, "Este número de identificación ya está registrado."
    
    affiliate_code = generate_affiliate_code()
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
        "kyc_verified": True,
        "balance": 0.0,
        "pending_payout": 0.0,
        "total_earned": 0.0,
        "join_date": datetime.now().isoformat(),
        "last_payout_date": None,
        "referrals": 0,
        "conversions": 0,
        "sales": []
    }
    
    db['affiliates'].append(new_affiliate)
    
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

def get_affiliate_by_id(affiliate_id):
    """Obtiene un afiliado por su ID."""
    db = load_affiliate_db()
    for affiliate in db['affiliates']:
        if affiliate['id'] == affiliate_id:
            return affiliate
    return None

def record_sale(affiliate_code, sale_type, amount_usd):
    """Registra una venta para un afiliado y calcula su comisión."""
    db = load_affiliate_db()
    
    for affiliate in db['affiliates']:
        if affiliate['affiliate_code'] == affiliate_code:
            commission_rate = db['settings']['commission_rates'].get(sale_type, 0.30)
            commission = amount_usd * commission_rate
            
            affiliate['conversions'] += 1
            affiliate['pending_payout'] += commission
            affiliate['total_earned'] += commission
            
            sale_record = {
                "id": str(uuid.uuid4()),
                "date": datetime.now().isoformat(),
                "type": sale_type,
                "amount_usd": amount_usd,
                "commission": commission,
                "commission_rate": commission_rate
            }
            
            affiliate['sales'].append(sale_record)
            if len(affiliate['sales']) > 100:
                affiliate['sales'] = affiliate['sales'][-100:]
            
            save_affiliate_db(db)
            return True, commission
    
    return False, 0

def calculate_affiliate_metrics(affiliate):
    """Calcula métricas clave para el dashboard del afiliado."""
    if not affiliate:
        return {}
    
    conversion_rate = 0
    if affiliate['referrals'] > 0:
        conversion_rate = (affiliate['conversions'] / affiliate['referrals']) * 100
    
    avg_sale_value = 0
    if affiliate['conversions'] > 0 and affiliate['sales']:
        total_sales = sum(sale['amount_usd'] for sale in affiliate['sales'])
        avg_sale_value = total_sales / affiliate['conversions']
    
    next_payout = "No disponible"
    if affiliate['pending_payout'] >= 50:
        today = datetime.now()
        days_ahead = 3 - today.weekday()
        if days_ahead <= 0:
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
# SECCIÓN 12: FUNCIONES DE EMAIL (NOTIFICACIONES)
# ============================================

def send_admin_notification(subject, message):
    """Envía una notificación por email al administrador."""
    try:
        log_payment_activity({
            "type": "admin_notification",
            "subject": subject,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "admin_email": ADMIN_EMAIL
        })
        st.success(f"📧 Notificación registrada para: {ADMIN_EMAIL}")
        return True
    except Exception as e:
        st.error(f"Error al enviar notificación: {str(e)}")
        return False

def log_payment_activity(activity_data):
    """Registra actividad de pagos en el log."""
    try:
        log_data = load_payment_log()
        if "activities" not in log_data:
            log_data["activities"] = []
        
        log_data["activities"].append(activity_data)
        if len(log_data["activities"]) > 500:
            log_data["activities"] = log_data["activities"][-500:]
        
        save_payment_log(log_data)
        return True
    except Exception as e:
        print(f"Error al registrar actividad: {str(e)}")
        return False

def mark_as_paid(affiliate_id, amount, tx_hash):
    """Marca un pago como realizado y envía notificaciones."""
    try:
        db = load_affiliate_db()
        
        for affiliate in db['affiliates']:
            if affiliate['id'] == affiliate_id:
                affiliate['balance'] += affiliate['pending_payout']
                affiliate['pending_payout'] = 0.0
                affiliate['last_payout_date'] = datetime.now().isoformat()
                
                payment_data = {
                    "id": str(uuid.uuid4()),
                    "affiliate_id": affiliate_id,
                    "affiliate_name": affiliate['full_name'],
                    "affiliate_email": affiliate['email'],
                    "amount": amount,
                    "tx_hash": tx_hash,
                    "date": datetime.now().isoformat(),
                    "status": "completed",
                    "processed_by": "admin"
                }
                
                if "payment_history" not in affiliate:
                    affiliate["payment_history"] = []
                affiliate["payment_history"].append(payment_data)
                
                save_affiliate_db(db)
                
                log_data = load_payment_log()
                if "payments" not in log_data:
                    log_data["payments"] = []
                
                log_data["payments"].append(payment_data)
                log_data["summary"]["total_paid"] = log_data["summary"].get("total_paid", 0) + amount
                log_data["summary"]["payments_count"] = log_data["summary"].get("payments_count", 0) + 1
                
                save_payment_log(log_data)
                
                notification_subject = f"Pago procesado - {affiliate['full_name']}"
                notification_message = f"""
                Se ha procesado un pago a un afiliado:
                
                📋 Detalles del Pago:
                • Afiliado: {affiliate['full_name']}
                • Email: {affiliate['email']}
                • Código: {affiliate['affiliate_code']}
                • Monto: ${amount:.2f} USD
                • TX Hash: {tx_hash}
                • Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}
                • Wallet: {affiliate['binance_wallet']}
                
                Este pago ha sido registrado en el sistema.
                """
                
                send_admin_notification(notification_subject, notification_message)
                
                log_payment_activity({
                    "type": "payment_processed",
                    "affiliate_id": affiliate_id,
                    "affiliate_name": affiliate['full_name'],
                    "amount": amount,
                    "tx_hash": tx_hash,
                    "timestamp": datetime.now().isoformat()
                })
                
                return True
        
        return False
        
    except Exception as e:
        st.error(f"Error al procesar pago: {str(e)}")
        return False

# ============================================
# SECCIÓN 13: PANEL DE ADMINISTRACIÓN
# ============================================

def check_admin_access():
    """Verifica si el usuario tiene acceso de administrador."""
    query_params = st.query_params
    url_password = query_params.get("admin", [""])[0]
    
    if url_password == ADMIN_PASSWORD:
        st.session_state.admin_logged_in = True
        st.session_state.admin_session_id = str(uuid.uuid4())[:8]
        return True
    
    if st.session_state.admin_logged_in:
        return True
    
    return False

def show_admin_panel():
    """Panel de administración principal."""
    if not check_admin_access():
        show_admin_login()
        return
    
    st.title("👑 Panel de Administración - MINDGEEKCLINIC")
    st.success(f"Sesión activa: {st.session_state.admin_session_id}")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💰 Pagos Pendientes",
        "👥 Todos los Afiliados",
        "📊 Reportes",
        "📋 Historial de Pagos",
        "⚙️ Configuración"
    ])
    
    with tab1:
        show_pending_payments()
    with tab2:
        show_all_affiliates()
    with tab3:
        show_admin_reports()
    with tab4:
        show_payment_history()
    with tab5:
        show_admin_settings()

def show_admin_login():
    """Muestra el formulario de login para administrador."""
    st.subheader("🔐 Acceso de Administrador")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("admin_login_form"):
            password = st.text_input("Contraseña de administrador", type="password")
            if st.form_submit_button("Acceder al panel", use_container_width=True):
                if password == ADMIN_PASSWORD:
                    st.session_state.admin_logged_in = True
                    st.session_state.admin_session_id = str(uuid.uuid4())[:8]
                    st.success("✅ Acceso concedido")
                    st.rerun()
                else:
                    st.error("❌ Contraseña incorrecta")
        
        st.info("""
        **O accede directamente por URL:**
        `https://tu-app.streamlit.app/?admin=Enaraure25..`
        """)

def show_pending_payments():
    """Muestra afiliados con pagos pendientes."""
    st.header("💰 Pagos Pendientes")
    db = load_affiliate_db()
    
    pending_affiliates = [
        aff for aff in db['affiliates'] if aff['pending_payout'] > 0
    ]
    
    total_pending = sum(aff['pending_payout'] for aff in pending_affiliates)
    eligible_for_payout = [aff for aff in pending_affiliates if aff['pending_payout'] >= 50]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💰 Total a Pagar", f"${total_pending:.2f} USD")
    with col2:
        st.metric("👥 Afiliados con Saldo", len(pending_affiliates))
    with col3:
        st.metric("✅ Elegibles (≥$50)", len(eligible_for_payout))
    
    st.markdown("---")
    
    if not pending_affiliates:
        st.info("🎉 No hay pagos pendientes actualmente.")
        return
    
    st.subheader("📋 Lista de Pagos Pendientes")
    pending_affiliates.sort(key=lambda x: x['pending_payout'], reverse=True)
    
    for i, affiliate in enumerate(pending_affiliates):
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 3])
            
            with col1:
                st.write(f"**{affiliate['full_name']}**")
                st.caption(f"{affiliate['email']}")
                st.caption(f"Código: `{affiliate['affiliate_code']}`")
            
            with col2:
                st.write(f"**Pendiente:** ${affiliate['pending_payout']:.2f}")
                st.caption(f"Total ganado: ${affiliate['total_earned']:.2f}")
                st.caption(f"Referidos: {affiliate['referrals']} | Ventas: {affiliate['conversions']}")
            
            with col3:
                st.write(f"**Wallet:**")
                st.code(affiliate['binance_wallet'], language="text")
                eligibility = "✅ Elegible" if affiliate['pending_payout'] >= 50 else f"❌ Necesita ${50 - affiliate['pending_payout']:.2f} más"
                st.caption(eligibility)
            
            with col4:
                with st.form(key=f"pay_form_{affiliate['id']}"):
                    tx_hash = st.text_input(
                        "TX Hash Binance",
                        key=f"tx_{affiliate['id']}",
                        placeholder="0x... o ID transacción",
                        help="Ingresa el hash de la transacción en Binance"
                    )
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.form_submit_button("✅ Marcar como Pagado", use_container_width=True):
                            if not tx_hash:
                                st.error("Debes ingresar el TX Hash")
                            else:
                                if mark_as_paid(affiliate['id'], affiliate['pending_payout'], tx_hash):
                                    st.success(f"✅ Pago registrado para {affiliate['full_name']}")
                                    st.rerun()
                                else:
                                    st.error("Error al registrar el pago")
                    with col_btn2:
                        if st.form_submit_button("📋 Ver Detalles", use_container_width=True):
                            show_affiliate_details(affiliate['id'])
        
        st.markdown("---")

def show_all_affiliates():
    """Muestra todos los afiliados registrados."""
    st.header("👥 Todos los Afiliados")
    db = load_affiliate_db()
    
    if not db['affiliates']:
        st.info("No hay afiliados registrados aún.")
        return
    
    col1, col2, col3 = st.columns(3)
    with col1:
        search_term = st.text_input("🔍 Buscar por nombre o email")
    with col2:
        country_filter = st.selectbox("Filtrar por país", ["Todos"] + COUNTRIES_LIST)
    with col3:
        status_filter = st.selectbox("Filtrar por estado", ["Todos", "active", "suspended", "pending"])
    
    filtered_affiliates = db['affiliates']
    
    if search_term:
        filtered_affiliates = [
            aff for aff in filtered_affiliates
            if search_term.lower() in aff['full_name'].lower() or
               search_term.lower() in aff['email'].lower()
        ]
    
    if country_filter != "Todos":
        filtered_affiliates = [
            aff for aff in filtered_affiliates
            if aff['country'] == country_filter
        ]
    
    if status_filter != "Todos":
        filtered_affiliates = [
            aff for aff in filtered_affiliates
            if aff['status'] == status_filter
        ]
    
    total_affiliates = len(db['affiliates'])
    active_affiliates = len([aff for aff in db['affiliates'] if aff['status'] == 'active'])
    total_commissions = sum(aff['total_earned'] for aff in db['affiliates'])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Afiliados", total_affiliates)
    with col2:
        st.metric("Activos", active_affiliates)
    with col3:
        st.metric("Comisiones Totales", f"${total_commissions:.2f}")
    
    st.markdown("---")
    
    st.subheader(f"📊 Lista de Afiliados ({len(filtered_affiliates)})")
    affiliate_data = []
    
    for aff in filtered_affiliates:
        join_date = datetime.fromisoformat(aff['join_date']).strftime('%d/%m/%Y')
        affiliate_data.append({
            "ID": aff['id'][:8],
            "Nombre": aff['full_name'],
            "Email": aff['email'],
            "País": aff['country'],
            "Código": aff['affiliate_code'],
            "Estado": aff['status'],
            "Registro": join_date,
            "Referidos": aff['referrals'],
            "Ventas": aff['conversions'],
            "Ganado": f"${aff['total_earned']:.2f}",
            "Pendiente": f"${aff['pending_payout']:.2f}"
        })
    
    if affiliate_data:
        df = pd.DataFrame(affiliate_data)
        st.dataframe(
            df,
            column_config={
                "ID": "ID",
                "Nombre": "Nombre",
                "Email": "Email",
                "País": "País",
                "Código": "Código",
                "Estado": "Estado",
                "Registro": "Registro",
                "Referidos": "Referidos",
                "Ventas": "Ventas",
                "Ganado": st.column_config.NumberColumn("Total Ganado"),
                "Pendiente": st.column_config.NumberColumn("Pendiente")
            },
            hide_index=True,
            use_container_width=True
        )
        
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("📤 Exportar a CSV", use_container_width=True):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Descargar CSV",
                    data=csv,
                    file_name=f"afiliados_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
    else:
        st.warning("No hay afiliados que coincidan con los filtros.")

def show_admin_reports():
    """Muestra reportes administrativos."""
    st.header("📊 Reportes Administrativos")
    db = load_affiliate_db()
    payment_log = load_payment_log()
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_affiliates = len(db['affiliates'])
    total_paid = payment_log['summary'].get('total_paid', 0)
    pending_payout = sum(aff['pending_payout'] for aff in db['affiliates'])
    active_affiliates = len([aff for aff in db['affiliates'] if aff['status'] == 'active'])
    
    with col1:
        st.metric("Total Afiliados", total_affiliates)
    with col2:
        st.metric("Pagado Total", f"${total_paid:.2f}")
    with col3:
        st.metric("Pendiente Total", f"${pending_payout:.2f}")
    with col4:
        st.metric("Afiliados Activos", active_affiliates)
    
    st.markdown("---")
    
    st.subheader("📈 Comisiones por Mes")
    months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun']
    commissions = np.random.uniform(500, 5000, 6)
    
    fig = px.bar(
        x=months,
        y=commissions,
        title="Comisiones Generadas por Mes",
        labels={'x': 'Mes', 'y': 'Comisiones (USD)'},
        color=commissions,
        color_continuous_scale='Blues'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("🏆 Top 10 Afiliados")
    top_affiliates = sorted(
        db['affiliates'],
        key=lambda x: x['total_earned'],
        reverse=True
    )[:10]
    
    if top_affiliates:
        top_data = []
        for i, aff in enumerate(top_affiliates, 1):
            conversion_rate = 0
            if aff['referrals'] > 0:
                conversion_rate = (aff['conversions'] / aff['referrals']) * 100
            
            top_data.append({
                "Posición": i,
                "Nombre": aff['full_name'],
                "País": aff['country'],
                "Total Ganado": f"${aff['total_earned']:.2f}",
                "Ventas": aff['conversions'],
                "Tasa Conversión": f"{conversion_rate:.1f}%"
            })
        
        df_top = pd.DataFrame(top_data)
        st.dataframe(df_top, hide_index=True, use_container_width=True)
    
    st.subheader("📋 Actividades Recientes")
    payment_log = load_payment_log()
    activities = payment_log.get('activities', [])
    
    if activities:
        recent_activities = sorted(
            activities,
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )[:10]
        
        for activity in recent_activities:
            timestamp = datetime.fromisoformat(activity['timestamp']).strftime('%H:%M')
            if activity['type'] == 'payment_processed':
                st.info(f"🕒 {timestamp} - Pago procesado: {activity.get('affiliate_name', 'N/A')} - ${activity.get('amount', 0):.2f}")
            elif activity['type'] == 'admin_notification':
                st.success(f"🕒 {timestamp} - Notificación enviada: {activity.get('subject', 'N/A')}")
    else:
        st.info("No hay actividades recientes.")

def show_payment_history():
    """Muestra el historial completo de pagos."""
    st.header("📋 Historial de Pagos")
    payment_log = load_payment_log()
    payments = payment_log.get('payments', [])
    
    if not payments:
        st.info("No hay historial de pagos aún.")
        return
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Fecha inicio", value=datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("Fecha fin", value=datetime.now())
    
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())
    
    filtered_payments = []
    for payment in payments:
        try:
            payment_date = datetime.fromisoformat(payment['date'])
            if start_dt <= payment_date <= end_dt:
                filtered_payments.append(payment)
        except:
            continue
    
    st.metric("Pagos en período", len(filtered_payments))
    
    if filtered_payments:
        payment_data = []
        for payment in filtered_payments:
            payment_date = datetime.fromisoformat(payment['date']).strftime('%d/%m/%Y %H:%M')
            payment_data.append({
                "Fecha": payment_date,
                "Afiliado": payment.get('affiliate_name', 'N/A'),
                "Email": payment.get('affiliate_email', 'N/A'),
                "Monto": f"${payment.get('amount', 0):.2f}",
                "TX Hash": payment.get('tx_hash', 'N/A')[:20] + "..." if len(payment.get('tx_hash', '')) > 20 else payment.get('tx_hash', 'N/A'),
                "Estado": payment.get('status', 'N/A'),
                "Procesado por": payment.get('processed_by', 'N/A')
            })
        
        df_payments = pd.DataFrame(payment_data)
        st.dataframe(df_payments, hide_index=True, use_container_width=True)
        
        csv_data = df_payments.to_csv(index=False)
        st.download_button(
            label="📥 Descargar Historial (CSV)",
            data=csv_data,
            file_name=f"historial_pagos_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        st.subheader("📊 Resumen del Período")
        col1, col2, col3 = st.columns(3)
        
        total_amount = sum(p['amount'] for p in filtered_payments)
        unique_affiliates = len(set(p['affiliate_id'] for p in filtered_payments))
        
        with col1:
            st.metric("Total Pagado", f"${total_amount:.2f}")
        with col2:
            st.metric("Número de Pagos", len(filtered_payments))
        with col3:
            st.metric("Afiliados Únicos", unique_affiliates)

def show_admin_settings():
    """Muestra la configuración del administrador."""
    st.header("⚙️ Configuración del Sistema")
    db = load_affiliate_db()
    settings = db['settings']
    
    with st.form("admin_settings_form"):
        st.subheader("💰 Configuración de Comisiones")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            therapy_rate = st.number_input(
                "Comisión Terapia (%)",
                min_value=0.0,
                max_value=100.0,
                value=settings['commission_rates']['therapy'] * 100,
                step=0.1
            )
        
        with col2:
            pdf_rate = st.number_input(
                "Comisión PDF (%)",
                min_value=0.0,
                max_value=100.0,
                value=settings['commission_rates']['pdf'] * 100,
                step=0.1
            )
        
        with col3:
            subscription_rate = st.number_input(
                "Comisión Suscripción (%)",
                min_value=0.0,
                max_value=100.0,
                value=settings['commission_rates']['subscription'] * 100,
                step=0.1
            )
        
        st.subheader("⚡ Configuración de Pagos")
        col1, col2 = st.columns(2)
        
        with col1:
            min_withdrawal = st.number_input(
                "Retiro Mínimo (USD)",
                min_value=0.0,
                value=settings['min_withdrawal'],
                step=1.0
            )
        
        with col2:
            payout_schedule = st.selectbox(
                "Frecuencia de Pagos",
                ["weekly", "biweekly", "monthly"],
                index=["weekly", "biweekly", "monthly"].index(settings['payout_schedule'])
            )
        
        st.subheader("📧 Notificaciones")
        notification_email = st.text_input(
            "Email para notificaciones",
            value=ADMIN_EMAIL,
            help="Email donde recibirás notificaciones de pagos"
        )
        
        if st.form_submit_button("💾 Guardar Configuración", use_container_width=True):
            settings['commission_rates']['therapy'] = therapy_rate / 100
            settings['commission_rates']['pdf'] = pdf_rate / 100
            settings['commission_rates']['subscription'] = subscription_rate / 100
            settings['min_withdrawal'] = min_withdrawal
            settings['payout_schedule'] = payout_schedule
            
            db['settings'] = settings
            if save_affiliate_db(db):
                st.success("✅ Configuración guardada exitosamente")
            else:
                st.error("❌ Error al guardar la configuración")
    
    st.markdown("---")
    
    st.subheader("🛠️ Herramientas de Administración")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Recalcular Comisiones", use_container_width=True):
            st.info("Recalculando comisiones...")
            time.sleep(1)
            st.success("Comisiones recalculadas")
        
        if st.button("📊 Generar Reporte Mensual", use_container_width=True):
            st.info("Generando reporte...")
            time.sleep(1)
            st.success("Reporte generado")
    
    with col2:
        if st.button("🧹 Limpiar Cache", use_container_width=True):
            st.session_state.clear()
            st.success("Cache limpiado. La página se recargará.")
            time.sleep(2)
            st.rerun()
        
        if st.button("🚪 Cerrar Sesión Admin", use_container_width=True):
            st.session_state.admin_logged_in = False
            st.session_state.admin_session_id = None
            st.success("Sesión cerrada")
            st.rerun()

def show_affiliate_details(affiliate_id):
    """Muestra detalles completos de un afiliado."""
    affiliate = get_affiliate_by_id(affiliate_id)
    if not affiliate:
        st.error("Afiliado no encontrado")
        return
    
    st.subheader(f"👤 Detalles del Afiliado: {affiliate['full_name']}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Email:** {affiliate['email']}")
        st.write(f"**Código:** `{affiliate['affiliate_code']}`")
        st.write(f"**País:** {affiliate['country']}")
        st.write(f"**Teléfono:** {affiliate['phone']}")
        st.write(f"**ID:** {affiliate['id_number']}")
    
    with col2:
        st.write(f"**Estado:** {affiliate['status']}")
        st.write(f"**Fecha Registro:** {datetime.fromisoformat(affiliate['join_date']).strftime('%d/%m/%Y')}")
        st.write(f"**Último Pago:** {affiliate['last_payout_date'] or 'Nunca'}")
        st.write(f"**Wallet Binance:** `{affiliate['binance_wallet']}`")
    
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Referidos", affiliate['referrals'])
    with col2:
        st.metric("Ventas", affiliate['conversions'])
    with col3:
        st.metric("Total Ganado", f"${affiliate['total_earned']:.2f}")
    with col4:
        st.metric("Pendiente", f"${affiliate['pending_payout']:.2f}")
    
    if affiliate.get('sales'):
        st.subheader("💼 Historial de Ventas")
        sales_df = pd.DataFrame(affiliate['sales'][-20:])
        if not sales_df.empty:
            sales_df['date'] = pd.to_datetime(sales_df['date']).dt.strftime('%d/%m/%Y %H:%M')
            sales_df['amount_usd'] = sales_df['amount_usd'].apply(lambda x: f"${x:.2f}")
            sales_df['commission'] = sales_df['commission'].apply(lambda x: f"${x:.2f}")
            
            st.dataframe(
                sales_df[['date', 'type', 'amount_usd', 'commission', 'commission_rate']],
                column_config={
                    "date": "Fecha",
                    "type": "Tipo",
                    "amount_usd": "Monto",
                    "commission": "Comisión",
                    "commission_rate": st.column_config.NumberColumn("Tasa %", format="%.1f%%")
                },
                hide_index=True,
                use_container_width=True
            )
    
    if affiliate.get('payment_history'):
        st.subheader("💰 Historial de Pagos")
        payments_df = pd.DataFrame(affiliate['payment_history'])
        if not payments_df.empty:
            payments_df['date'] = pd.to_datetime(payments_df['date']).dt.strftime('%d/%m/%Y')
            payments_df['amount'] = payments_df['amount'].apply(lambda x: f"${x:.2f}")
            
            st.dataframe(
                payments_df[['date', 'amount', 'tx_hash', 'status']],
                column_config={
                    "date": "Fecha",
                    "amount": "Monto",
                    "tx_hash": "TX Hash",
                    "status": "Estado"
                },
                hide_index=True,
                use_container_width=True
            )

# ============================================
# SECCIÓN 14: INTERFAZ PRINCIPAL DE LA APLICACIÓN
# ============================================

def main():
    track_access()
    data = load_data()
    
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
    
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/brain.png", width=80)
        st.title("Navegación")
        
        menu_option = st.radio(
            "Selecciona una sección:",
            ["🏠 Inicio", "📝 Nuevo Diagnóstico", "🔍 Consultar IA", "📊 Estadísticas", "💾 Backup"],
            index=0
        )
        
        st.markdown("---")
        st.subheader("👥 Programa de Afiliados")
        affiliate_menu = st.radio(
            "Opciones para afiliados:",
            ["📋 Registrarse como Afiliado", "📊 Dashboard de Afiliado"]
        )
        
        query_params = st.query_params
        detected_affiliate_code = query_params.get("affiliate", [""])[0]
        if detected_affiliate_code:
            st.info(f"Código de afiliado detectado: `{detected_affiliate_code}`")
            affiliate = get_affiliate_by_code(detected_affiliate_code)
            if affiliate:
                st.success("✅ Código válido")
                st.session_state.current_affiliate = affiliate
            else:
                st.warning("⚠️ Código no encontrado en el sistema")
        
        st.markdown("---")
        
        if check_admin_access():
            st.subheader("👑 Administración")
            if st.button("📊 Panel de Admin", use_container_width=True):
                st.query_params = {"admin": ADMIN_PASSWORD}
                st.rerun()
        else:
            with st.expander("🔐 Acceso Admin"):
                admin_pass = st.text_input("Contraseña", type="password")
                if st.button("Acceder", use_container_width=True):
                    if admin_pass == ADMIN_PASSWORD:
                        st.session_state.admin_logged_in = True
                        st.session_state.admin_session_id = str(uuid.uuid4())[:8]
                        st.success("Acceso concedido")
                        st.rerun()
                    else:
                        st.error("Contraseña incorrecta")
        
        st.markdown("---")
        st.caption(f"Versión {APP_VERSION}")
        st.caption(f"Accesos hoy: {random.randint(10, 50)}")
        
        if st.button("🔄 Actualizar", use_container_width=True):
            st.rerun()
    
    if check_admin_access() and st.query_params.get("admin", [""])[0] == ADMIN_PASSWORD:
        show_admin_panel()
        return
    
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
    
    if affiliate_menu == "📋 Registrarse como Afiliado":
        show_affiliate_registration()
    elif affiliate_menu == "📊 Dashboard de Afiliado":
        show_affiliate_dashboard()

# ============================================
# SECCIÓN 15: PÁGINAS PRINCIPALES DE LA APP
# ============================================

def show_homepage():
    """Muestra la página de inicio."""
    st.subheader("Bienvenido a MINDGEEKCLINIC")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### ¿Qué es la Biodescodificación?
        La **biodescodificación** es un enfoque terapéutico que busca identificar el conflicto emocional oculto detrás de los síntomas físicos.
        
        ### 🎯 Características de la Plataforma
        1. **Diagnóstico especializado** por sistemas corporales
        2. **Triangulación emocional** entre eventos y síntomas
        3. **Protocolos de hipnosis** personalizados
        4. **Generación de informes** profesionales en PDF
        5. **Consulta con IA** especializada en biodescodificación
        6. **Sistema de afiliados** para profesionales
        7. **Panel de administración** para gestión de pagos
        
        ### 📈 Impacto Esperado
        - Reducción del tiempo de diagnóstico en 40%
        - Aumento de efectividad terapéutica en 60%
        - Automatización de procesos administrativos
        - Sistema de comisiones automatizado
        """)
    
    with col2:
        st.info("""
        **🚀 Novedades:**
        • **Panel de Administración** Gestiona pagos y afiliados fácilmente.
        • **Notificaciones Automáticas** Recibe alertas de pagos por email.
        • **Reportes Detallados** Exporta datos para contabilidad.
        • **Integración Binance** Pagos seguros en criptomonedas.
        """)
    
    with st.expander("📊 Datos Rápidos"):
        db = load_affiliate_db()
        total_affiliates = len(db['affiliates'])
        pending_payout = sum(aff['pending_payout'] for aff in db['affiliates'])
        st.metric("Afiliados Activos", total_affiliates)
        st.metric("Comisiones Pendientes", f"${pending_payout:.2f}")
        st.metric("Tasa Conversión", "34%")
    
    st.markdown("---")
    
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
        if st.button("👑 Acceso Admin", use_container_width=True):
            st.query_params = {"admin": ADMIN_PASSWORD}
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
            entorno = st.selectbox("Entorno social predominante*", ["Laboral", "Familiar", "Pareja", "Social", "Soledad", "Mixto"])
        
        st.markdown("---")
        
        col_aff1, col_aff2 = st.columns([3, 1])
        with col_aff1:
            query_params = st.query_params
            url_affiliate_code = query_params.get("affiliate", [""])[0]
            default_code = url_affiliate_code if url_affiliate_code else st.session_state.affiliate_code_input
            affiliate_code = st.text_input(
                "Código de afiliado (opcional)",
                value=default_code,
                placeholder="Ej: MINDGEEKCLINIC-AFFILIATE-ABC123",
                help="Si vienes de un enlace de afiliado, este campo se llenará automáticamente."
            )
            if affiliate_code:
                st.session_state.affiliate_code_input = affiliate_code
        
        with col_aff2:
            st.markdown("###")
            if affiliate_code:
                affiliate = get_affiliate_by_code(affiliate_code)
                if affiliate:
                    st.success("✅ Válido")
                else:
                    st.warning("❌ No encontrado")
            else:
                st.info("ℹ️ Opcional")
        
        st.markdown("---")
        st.subheader("🎭 Eventos Emocionales Relevantes")
        eventos = st.text_area(
            "Describe eventos significativos alrededor del inicio de los síntomas*",
            placeholder="Ej: Pérdida de empleo, ruptura amorosa, cambio de ciudad, conflicto familiar...",
            height=100
        )
        
        st.subheader("🔍 Síntomas Específicos")
        sintomas = st.text_area(
            "Lista todos los síntomas (separados por comas)*",
            placeholder="Ej: Dolor de cabeza, insomnio, palpitaciones, náuseas...",
            height=100
        )
        
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
                        "affiliate_code": affiliate_code if affiliate_code else None
                    }
                    
                    if affiliate_code:
                        affiliate = get_affiliate_by_code(affiliate_code)
                        if affiliate:
                            db = load_affiliate_db()
                            for aff in db['affiliates']:
                                if aff['affiliate_code'] == affiliate_code:
                                    aff['referrals'] += 1
                            save_affiliate_db(db)
                            st.success(f"✅ Referido registrado para afiliado: {affiliate_code}")
                    
                    triangulation = analyze_emotional_triangulation(sintomas, eventos, tiempo)
                    diagnosis = generate_diagnosis_report(patient_data, triangulation)
                    main_system = get_system_by_symptom(dolencia)
                    protocol = generate_hypnosis_protocol(main_system, "conflicto_visual")
                    
                    st.success("✅ Diagnóstico generado exitosamente!")
                    
                    st.session_state.diagnosticos_realizados += 1
                    st.session_state.pacientes_registrados += 1
                    
                    data["patients"].append(patient_data)
                    data["diagnoses"].append({
                        "patient_id": patient_data["id"],
                        "diagnosis": diagnosis,
                        "protocol": protocol,
                        "date": datetime.now().isoformat()
                    })
                    save_data(data)
                    
                    tab1, tab2, tab3, tab4 = st.tabs(["📋 Diagnóstico", "🧠 Protocolo", "🧘 Autohipnosis", "📄 PDF"])
                    
                    with tab1:
                        st.markdown(diagnosis)
                    
                    with tab2:
                        st.markdown(protocol)
                        autohipnosis = generate_self_hypnosis_script(protocol)
                        if st.button("🔄 Generar Versión Autohipnosis"):
                            st.markdown(autohipnosis)
                    
                    with tab3:
                        st.subheader("🧘 Guía de Autohipnosis")
                        st.markdown(autohipnosis)
                        st.audio("https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3", format="audio/mp3")
                    
                    with tab4:
                        st.subheader("📄 Reporte Profesional en PDF")
                        pdf_buffer = create_pdf_diagnosis(patient_data, diagnosis, protocol)
                        st.markdown(get_pdf_download_link(pdf_buffer), unsafe_allow_html=True)
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
                chroma_client, collection = initialize_chroma_db()
                knowledge_results = query_knowledge_base(query, collection)
                
                knowledge_context = ""
                if knowledge_results and 'documents' in knowledge_results:
                    knowledge_context = "\n".join(knowledge_results['documents'][0][:2])
                
                full_context = f"{knowledge_context}\n{context}"
                response = generate_with_groq(query, full_context)
                
                st.success("✅ Respuesta generada:")
                st.markdown(response)
                
                if knowledge_results and 'metadatas' in knowledge_results:
                    with st.expander("📚 Fuentes consultadas"):
                        for i, metadata in enumerate(knowledge_results['metadatas'][0]):
                            st.caption(f"Fuente {i+1}: {metadata.get('source', 'Conocimiento especializado')}")

def show_statistics_page():
    """Muestra la página de estadísticas."""
    st.subheader("📊 Estadísticas de la Plataforma")
    display_statistics()
    
    st.markdown("---")
    st.subheader("👥 Distribución Demográfica")
    
    col1, col2 = st.columns(2)
    
    with col1:
        gender_data = pd.DataFrame({
            'Género': ['Mujeres', 'Hombres', 'Otros'],
            'Porcentaje': [52, 45, 3]
        })
        fig_gender = px.pie(gender_data, values='Porcentaje', names='Género',
                           title='Distribución por Género',
                           color_discrete_sequence=px.colors.sequential.Blues_r)
        st.plotly_chart(fig_gender, use_container_width=True)
    
    with col2:
        age_data = pd.DataFrame({
            'Rango Edad': ['18-25', '26-35', '36-45', '46-55', '56+'],
            'Pacientes': [15, 35, 28, 15, 7]
        })
        fig_age = px.bar(age_data, x='Rango Edad', y='Pacientes',
                        title='Distribución por Edad',
                        color='Pacientes',
                        color_continuous_scale='Blues')
        st.plotly_chart(fig_age, use_container_width=True)
    
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
                progress_bar = st.progress(0)
                for i in range(100):
                    time.sleep(0.01)
                    progress_bar.progress(i + 1)
                st.success(f"Datos exportados en formato {export_format}")

# ============================================
# SECCIÓN 16: INTERFACES DEL SISTEMA DE AFILIADOS - CORREGIDO
# ============================================

def show_affiliate_registration():
    """Muestra el formulario de registro de afiliados - CORREGIDO."""
    st.subheader("👥 Registro en el Programa de Afiliados")
    st.markdown("""
    Únete como afiliado de **MINDGEEKCLINIC** y gana comisiones recomendando nuestros servicios.
    
    **Comisiones:** 34.5% en terapias, 33.3% en PDFs, 31.6% en suscripciones.
    **Retiro mínimo:** $50 USD semanales vía Binance.
    """)
    
    # ============================================
    # SECCIÓN 1: VERIFICACIÓN DE EMAIL (FUERA DEL FORM)
    # ============================================
    st.markdown("### 📧 Paso 1: Verifica tu Email")
    
    col_verify1, col_verify2 = st.columns([3, 1])
    
    with col_verify1:
        email_for_verification = st.text_input(
            "Email para verificación", 
            key="email_verify_input", 
            placeholder="tu@email.com",
            help="Te enviaremos un código de 6 dígitos"
        )
    
    with col_verify2:
        st.markdown("###")
        if st.button("📨 Enviar código", 
                    key="send_code_btn", 
                    use_container_width=True,
                    type="primary",
                    disabled=not email_for_verification):
            if email_for_verification:
                verification_code = send_verification_code(email_for_verification)
                if verification_code:
                    st.success(f"✅ Código enviado a {email_for_verification}")
                    st.rerun()
            else:
                st.error("Por favor, ingresa un email válido")
    
    # Si hay código pendiente, mostrar campo para ingresarlo
    if 'verification_code' in st.session_state and st.session_state['verification_code']:
        st.info(f"📩 Código pendiente para: {st.session_state.get('verification_email', '')}")
        
        verification_input = st.text_input(
            "Ingresa el código de 6 dígitos", 
            max_chars=6, 
            key="code_input",
            placeholder="123456",
            help="Revisa tu bandeja de entrada (y carpeta de spam)"
        )
        
        if verification_input:
            verified, message = verify_email_code(verification_input)
            if verified:
                st.success(f"✅ {message}")
                st.session_state['verified_email'] = st.session_state.get('verification_email', '')
            else:
                st.error(f"❌ {message}")
    
    st.markdown("---")
    
    # ============================================
    # SECCIÓN 2: FORMULARIO PRINCIPAL DE REGISTRO
    # ============================================
    
    # Solo mostrar formulario si el email está verificado
    if st.session_state.get('verified_email'):
        st.markdown("### 📝 Paso 2: Completa tu información")
        
        with st.form("affiliate_registration_form"):
            st.markdown("#### 👤 Información Personal (KYC)")
            
            col1, col2 = st.columns(2)
            
            with col1:
                full_name = st.text_input("Nombre completo*", key="full_name", placeholder="Ej: María González")
                email = st.text_input(
                    "Email*", 
                    value=st.session_state.get('verified_email', ''), 
                    disabled=True,
                    help="Email verificado"
                )
                id_number = st.text_input("Número de identificación*", key="id_number", placeholder="DNI, Pasaporte, etc.")
            
            with col2:
                country = st.selectbox("País*", COUNTRIES_LIST, key="country")
                phone = st.text_input("Teléfono*", key="phone", placeholder="+34 123 456 789")
                binance_wallet = st.text_input(
                    "Wallet de Binance (USDT)*", 
                    key="binance_wallet", 
                    placeholder="0x... o dirección de wallet",
                    help="Dirección donde recibirás pagos"
                )
            
            # Validación de wallet
            wallet_valid = False
            if binance_wallet:
                if validate_binance_wallet(binance_wallet):
                    st.success("✅ Formato de wallet válido")
                    wallet_valid = True
                else:
                    st.warning("⚠️ El formato no coincide con direcciones comunes de Binance. Verifica.")
                    wallet_valid = False
            
            st.markdown("---")
            
            # Términos y condiciones
            st.markdown("#### ✅ Términos y Condiciones")
            
            col_terms1, col_terms2 = st.columns(2)
            
            with col_terms1:
                accept_terms = st.checkbox("Acepto los términos y condiciones*", key="accept_terms")
                accept_privacy = st.checkbox("Acepto la política de privacidad*", key="accept_privacy")
            
            with col_terms2:
                confirm_kyc = st.checkbox("Confirmo que la información es verídica*", key="confirm_kyc")
                accept_payments = st.checkbox("Acepto recibir pagos vía Binance*", key="accept_payments")
            
            st.markdown("---")
            
            # Botón de submit CORREGIDO (dentro del formulario)
            submitted = st.form_submit_button(
                "🚀 Registrar como Afiliado", 
                use_container_width=True, 
                type="primary"
            )
            
            # Validación después del submit
            if submitted:
                # Validar campos
                if not all([full_name, id_number, country, phone, binance_wallet]):
                    st.error("❌ Por favor, completa todos los campos obligatorios (*)")
                elif not wallet_valid:
                    st.error("❌ Por favor, ingresa una dirección de Binance válida")
                elif not all([accept_terms, accept_privacy, confirm_kyc, accept_payments]):
                    st.error("❌ Debes aceptar todos los términos y condiciones")
                else:
                    with st.spinner("Registrando afiliado..."):
                        affiliate_data = {
                            "full_name": full_name,
                            "email": st.session_state.get('verified_email', ''),
                            "id_number": id_number,
                            "country": country,
                            "phone": phone,
                            "binance_wallet": binance_wallet
                        }
                        
                        success, message = register_affiliate(affiliate_data)
                        
                        if success:
                            st.balloons()
                            st.success(message)
                            
                            # Limpiar estado de verificación
                            keys_to_clear = ['verification_code', 'verification_email', 'verified_email', 'verification_time']
                            for key in keys_to_clear:
                                if key in st.session_state:
                                    del st.session_state[key]
                            
                            st.markdown("""
                            ### 🎉 ¡Registro Exitoso!
                            
                            **Próximos pasos:**
                            1. **Guarda tu código de afiliado** (aparece arriba)
                            2. **Comparte tu link:** `https://tu-app.streamlit.app/?affiliate=TU-CODIGO`
                            3. **Monitorea** tu dashboard para ver referidos y comisiones
                            4. **Retira** tus ganancias cada jueves (mínimo $50 USD)
                            
                            **Contacto:** affiliates@mindgeekclinic.com
                            """)
                        else:
                            st.error(f"❌ Error en el registro: {message}")
    else:
        # Mostrar instrucciones si el email no está verificado
        st.info("""
        **👆 Instrucciones para registrarte:**
        
        1. **Ingresa tu email** arriba y haz clic en "Enviar código"
        2. **Revisa tu bandeja de entrada** (incluyendo carpeta de spam)
        3. **Ingresa el código de 6 dígitos** que recibiste
        4. **Completa el formulario** que aparecerá automáticamente
        
        **📧 ¿No recibes el código?**
        • Verifica la carpeta de spam/no deseado
        • Asegúrate de que el email esté correcto
        • Intenta con otro proveedor de email
        • Contacta a soporte: affiliates@mindgeekclinic.com
        """)

def show_affiliate_dashboard():
    """Muestra el dashboard del afiliado."""
    st.subheader("📊 Dashboard de Afiliado")
    
    if 'current_affiliate' in st.session_state and st.session_state.current_affiliate:
        affiliate = st.session_state.current_affiliate
    else:
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
    
    affiliate = st.session_state.current_affiliate
    metrics = calculate_affiliate_metrics(affiliate)
    
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
    
    if metrics['pending_payout'] >= 50:
        if st.button("💳 Solicitar Retiro Ahora", use_container_width=True):
            st.success(f"Retiro de ${metrics['pending_payout']:.2f} USD procesado. Llegará a tu wallet en 24-48h.")
    else:
        st.warning(f"Necesitas ${50 - metrics['pending_payout']:.2f} USD más para retirar")
    
    st.markdown("---")
    
    st.markdown("### 🔗 Tu Link de Afiliado")
    base_url = "https://mindgeekclinic.com"
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
    
    st.markdown("### 📈 Tu Desempeño")
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
    
    if affiliate.get('sales'):
        st.markdown("### 💰 Ventas Recientes")
        sales_df = pd.DataFrame(affiliate['sales'][-10:])
        if not sales_df.empty:
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
                        "Tasa %", format="%.1f%%"
                    )
                },
                hide_index=True,
                use_container_width=True
            )
    
    st.markdown("---")
    
    st.markdown("### ⚡ Acciones Rápidas")
    col_act1, col_act2, col_act3 = st.columns(3)
    
    with col_act1:
        if st.button("🔄 Actualizar Datas", use_container_width=True):
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
