import streamlit as st
import os
import zipfile
import tempfile
from pathlib import Path
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain.chains import RetrievalQA  # ¡CORREGIDO! Era langchain_classic
import requests
import json
from datetime import datetime
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import hashlib
import logging

# ================= CONFIGURACIÓN SEGURA =================
# ✅ TODAS LAS CLAVES VAN EN SECRETS, NO EN EL CÓDIGO
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")  # Configurar en Secrets
ZIP_URL = "https://github.com/alkhimiya/mindgeekclinicdeployment/raw/refs/heads/main/mindgeekclinic_db.zip"

# Configuración de email
EMAIL_CONFIG = {
    "smtp_server": st.secrets.get("SMTP_SERVER", "smtp.gmail.com"),
    "smtp_port": int(st.secrets.get("SMTP_PORT", 587)),
    "sender_email": st.secrets.get("SENDER_EMAIL", ""),
    "sender_password": st.secrets.get("SENDER_PASSWORD", "")
}

# Configuración de reintentos
RETRY_CONFIG = {
    "max_retries": 3,
    "delay_seconds": 2,
    "backoff_factor": 1.5
}

# ================= CONFIGURACIÓN DE IDIOMAS =================
IDIOMAS_DISPONIBLES = {
    "es": {"nombre": "Español", "emoji": "🇪🇸"},
    "en": {"nombre": "English", "emoji": "🇺🇸"},
    "pt": {"nombre": "Português", "emoji": "🇧🇷"},
    "fr": {"nombre": "Français", "emoji": "🇫🇷"},
    "de": {"nombre": "Deutsch", "emoji": "🇩🇪"},
    "it": {"nombre": "Italiano", "emoji": "🇮🇹"}
}

# Textos traducidos
TEXTOS = {
    "es": {
        "titulo": "🧠 MINDGEEKCLINIC",
        "subtitulo": "Sistema Profesional de Biodescodificación",
        "consentimiento_titulo": "CONSENTIMIENTO INFORMADO Y PROTECCIÓN DE DATOS",
        "consentimiento_texto": """
        **DECLARACIÓN DE CONSENTIMIENTO INFORMADO**
        
        Al utilizar este servicio, usted reconoce y acepta que:
        
        1. **Datos Sensibles:** La información proporcionada incluye datos de salud considerados sensibles.
        2. **Almacenamiento Seguro:** Sus datos se almacenarán de manera cifrada y segura en nuestra historia clínica digital.
        3. **Confidencialidad:** Su información será tratada con estricta confidencialidad profesional.
        4. **Finalidades:**
           - Diagnóstico y tratamiento mediante biodescodificación
           - Mejora continua del sistema asistencial
           - Envío de información sobre servicios, eventos y promociones relacionadas
        5. **Derechos:** Usted tiene derecho a acceder, rectificar y cancelar sus datos en cualquier momento.
        6. **Protección:** Cumplimos con estándares internacionales de protección de datos de salud.
        
        Su privacidad es nuestra prioridad. Los datos se utilizarán únicamente para los fines descritos.
        """,
        "acepto": "✅ He leído y ACEPTO el consentimiento informado",
        "form_titulo": "📋 FORMULARIO DE EVALUACIÓN CLÍNICA",
        "iniciales": "📝 **Iniciales del nombre**",
        "edad": "🎂 **Edad**",
        "email": "📧 **Correo electrónico**",
        "enviar": "🚀 **ANALIZAR Y ENVIAR DIAGNÓSTICO**",
        "email_placeholder": "ejemplo@correo.com",
        "email_help": "Recibirá el diagnóstico y podremos enviarle información relevante",
        "idioma_titulo": "🌍 **Idioma de preferencia**",
        "error_api_key": "❌ ERROR: Configura GROQ_API_KEY en Streamlit Cloud Secrets.",
        "sistema_cargando": "🔄 Cargando sistema especializado...",
        "diagnostico_generando": "🔄 Generando diagnóstico en su idioma..."
    },
    "en": {
        "titulo": "🧠 MINDGEEKCLINIC",
        "subtitulo": "Professional Biodescodification System",
        "consentimiento_titulo": "INFORMED CONSENT AND DATA PROTECTION",
        "consentimiento_texto": """
        **INFORMED CONSENT DECLARATION**
        
        By using this service, you acknowledge and accept that:
        
        1. **Sensitive Data:** The information provided includes health data considered sensitive.
        2. **Secure Storage:** Your data will be stored encrypted and securely in our digital clinical history.
        3. **Confidentiality:** Your information will be treated with strict professional confidentiality.
        4. **Purposes:**
           - Diagnosis and treatment through biodescodification
           - Continuous improvement of the assistance system
           - Sending information about related services, events, and promotions
        5. **Rights:** You have the right to access, rectify, and cancel your data at any time.
        6. **Protection:** We comply with international health data protection standards.
        
        Your privacy is our priority. Data will be used only for the described purposes.
        """,
        "acepto": "✅ I have READ and ACCEPT the informed consent",
        "form_titulo": "📋 CLINICAL EVALUATION FORM",
        "iniciales": "📝 **Name initials**",
        "edad": "🎂 **Age**",
        "email": "📧 **Email address**",
        "enviar": "🚀 **ANALYZE AND SEND DIAGNOSIS**",
        "email_placeholder": "example@email.com",
        "email_help": "You will receive the diagnosis and we can send you relevant information",
        "idioma_titulo": "🌍 **Preferred language**",
        "error_api_key": "❌ ERROR: Configure GROQ_API_KEY in Streamlit Cloud Secrets.",
        "sistema_cargando": "🔄 Loading specialized system...",
        "diagnostico_generando": "🔄 Generating diagnosis in your language..."
    }
}

# ================= SETUP LOGGING =================
def setup_logging():
    """Configura logging para diagnóstico."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('mindgeekclinic.log')
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# ================= FUNCIONES DE SEGURIDAD =================
def generar_id_seguro(datos):
    """Genera ID seguro y anónimo para el paciente."""
    cadena = f"{datos['iniciales']}{datos['edad']}{datos.get('email','')}{datetime.now().timestamp()}"
    return hashlib.sha256(cadena.encode()).hexdigest()[:16]

# ================= SISTEMA DE IDIOMAS =================
def detectar_idioma_texto(texto):
    """Detecta el idioma del texto ingresado."""
    if not texto:
        return "es"
    
    es_words = ['el', 'la', 'de', 'que', 'y', 'en', 'los', 'las']
    en_words = ['the', 'and', 'of', 'to', 'in', 'is', 'you', 'that']
    pt_words = ['o', 'a', 'de', 'que', 'e', 'em', 'os', 'as']
    fr_words = ['le', 'la', 'de', 'et', 'à', 'dans', 'les', 'des']
    de_words = ['der', 'die', 'das', 'und', 'in', 'den', 'von', 'zu']
    it_words = ['il', 'la', 'di', 'e', 'a', 'in', 'per', 'con']
    
    texto_lower = texto.lower()
    
    es_count = sum(1 for word in es_words if word in texto_lower)
    en_count = sum(1 for word in en_words if word in texto_lower)
    pt_count = sum(1 for word in pt_words if word in texto_lower)
    fr_count = sum(1 for word in fr_words if word in texto_lower)
    de_count = sum(1 for word in de_words if word in texto_lower)
    it_count = sum(1 for word in it_words if word in texto_lower)
    
    counts = {
        "es": es_count,
        "en": en_count,
        "pt": pt_count,
        "fr": fr_count,
        "de": de_count,
        "it": it_count
    }
    
    return max(counts, key=counts.get)

# ================= VERIFICACIÓN DEL SISTEMA =================
def verificar_sistema():
    """Verifica que todos los componentes estén funcionando."""
    checks = {
        "api_key": bool(GROQ_API_KEY),
        "zip_url_accesible": False,
        "modelo_disponible": False
    }
    
    try:
        # Verificar URL del ZIP
        response = requests.head(ZIP_URL, timeout=10)
        checks["zip_url_accesible"] = response.status_code == 200
        
        # Si tenemos API key, verificar modelo
        if GROQ_API_KEY:
            try:
                llm_test = ChatGroq(
                    groq_api_key=GROQ_API_KEY,
                    model_name="meta-llama/llama-4-scout-17b-16e-instruct",
                    temperature=0.1,
                    max_tokens=100
                )
                checks["modelo_disponible"] = True
            except Exception as e:
                logger.error(f"Error verificando modelo: {e}")
                checks["modelo_disponible"] = False
                
    except Exception as e:
        logger.error(f"Error verificación sistema: {e}")
        st.session_state.error_message = f"Error de conexión: {str(e)[:100]}"
    
    return checks

# ================= CONSENTIMIENTO INFORMADO =================
def mostrar_consentimiento(idioma="es"):
    """Muestra y gestiona el consentimiento informado."""
    textos = TEXTOS.get(idioma, TEXTOS["es"])
    
    with st.expander(f"📄 {textos['consentimiento_titulo']}", expanded=True):
        st.markdown(textos['consentimiento_texto'])
        
        col1, col2 = st.columns([3, 1])
        with col1:
            aceptado = st.checkbox(textos['acepto'], key=f"consent_{idioma}")
        with col2:
            if st.button("📋 Ver completo", key=f"ver_completo_{idioma}"):
                st.info("Política completa disponible en mindgeekclinic.com/privacidad")
        
        return aceptado

# ================= FORMULARIO MULTI-IDIOMA =================
def formulario_diagnostico(idioma="es"):
    """Muestra formulario clínico en el idioma seleccionado."""
    textos = TEXTOS.get(idioma, TEXTOS["es"])
    
    st.markdown(f"### {textos['form_titulo']}")
    
    with st.form("formulario_clinico"):
        # Selector de idioma
        col_idioma1, col_idioma2 = st.columns([2, 1])
        with col_idioma1:
            idioma_seleccionado = st.selectbox(
                textos['idioma_titulo'],
                options=list(IDIOMAS_DISPONIBLES.keys()),
                format_func=lambda x: f"{IDIOMAS_DISPONIBLES[x]['emoji']} {IDIOMAS_DISPONIBLES[x]['nombre']}",
                index=list(IDIOMAS_DISPONIBLES.keys()).index(idioma)
            )
        
        # Consentimiento (requerido)
        if not mostrar_consentimiento(idioma_seleccionado):
            st.error("❌ Debe aceptar el consentimiento informado para continuar.")
            st.stop()
        
        st.markdown("---")
        
        # Datos personales
        col1, col2 = st.columns(2)
        with col1:
            iniciales = st.text_input(
                textos['iniciales'],
                max_chars=3,
                help="Ej: JPG para Juan Pérez García" if idioma_seleccionado == "es" else "Ex: JPG for John P. Garcia"
            )
            edad = st.number_input(
                textos['edad'],
                min_value=1,
                max_value=120,
                value=30
            )
            estado_civil = st.selectbox(
                "💍 **Estado civil**" if idioma_seleccionado == "es" else "💍 **Marital status**",
                ["Soltero", "Casado", "Divorciado", "Viudo", "Unión libre", "Separado"] if idioma_seleccionado == "es" 
                else ["Single", "Married", "Divorced", "Widowed", "Domestic partnership", "Separated"]
            )
            
        with col2:
            situacion_laboral = st.selectbox(
                "💼 **Situación laboral**" if idioma_seleccionado == "es" else "💼 **Employment status**",
                ["Empleado", "Desempleado", "Independiente", "Estudiante", "Jubilado", "Incapacitado"] if idioma_seleccionado == "es"
                else ["Employed", "Unemployed", "Self-employed", "Student", "Retired", "Disabled"]
            )
            tension_alta = st.number_input(
                "🩺 **Tensión arterial alta**" if idioma_seleccionado == "es" else "🩺 **High blood pressure**",
                min_value=50,
                max_value=250,
                value=120
            )
            tension_baja = st.number_input(
                "🩺 **Tensión arterial baja**" if idioma_seleccionado == "es" else "🩺 **Low blood pressure**",
                min_value=30,
                max_value=150,
                value=80
            )
        
        # Email
        st.markdown("---")
        email = st.text_input(
            textos['email'],
            placeholder=textos['email_placeholder'],
            help=textos['email_help']
        )
        
        # Descripción del padecimiento
        st.markdown("---")
        st.markdown("#### 🤒 **Descripción del padecimiento**")
        descripcion = st.text_area(
            "Describa sus síntomas en su idioma preferido:" if idioma_seleccionado == "es" else "Describe your symptoms in your preferred language:",
            height=150,
            placeholder="Escriba aquí..." if idioma_seleccionado == "es" else "Write here..."
        )
        
        # Detectar idioma automáticamente
        idioma_detectado = detectar_idioma_texto(descripcion) if descripcion else idioma_seleccionado
        
        # Tiempo del padecimiento
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            tiempo_opciones = {
                "es": ["Menos de 1 mes", "1-3 meses", "3-6 meses", "6-12 meses", "1-2 años", "2-5 años", "Más de 5 años"],
                "en": ["Less than 1 month", "1-3 months", "3-6 months", "6-12 months", "1-2 years", "2-5 years", "More than 5 years"]
            }
            
            tiempo_padecimiento = st.selectbox(
                "⏳ **¿Desde hace cuánto tiempo?**" if idioma_seleccionado == "es" else "⏳ **How long have you had this?**",
                tiempo_opciones.get(idioma_seleccionado, tiempo_opciones["es"])
            )
        
        with col_t2:
            frecuencia_opciones = {
                "es": ["Constante", "Diariamente", "Varias veces por semana", "Semanalmente", "Mensualmente", "Ocasionalmente"],
                "en": ["Constant", "Daily", "Several times a week", "Weekly", "Monthly", "Occasionally"]
            }
            
            frecuencia = st.selectbox(
                "🔄 **Frecuencia**" if idioma_seleccionado == "es" else "🔄 **Frequency**",
                frecuencia_opciones.get(idioma_seleccionado, frecuencia_opciones["es"])
            )
        
        # Submit
        submitted = st.form_submit_button(
            textos['enviar'],
            type="primary",
            use_container_width=True
        )
        
        if submitted:
            if not email or "@" not in email:
                st.error("❌ Email válido requerido para el diagnóstico")
                return
            
            if not iniciales or len(iniciales.strip()) < 2:
                st.error("❌ Iniciales requeridas (mínimo 2 caracteres)")
                return
            
            datos_paciente = {
                "id_seguro": generar_id_seguro({"iniciales": iniciales, "edad": edad, "email": email}),
                "iniciales": iniciales.upper(),
                "edad": edad,
                "estado_civil": estado_civil,
                "situacion_laboral": situacion_laboral,
                "tension": f"{tension_alta}/{tension_baja}",
                "email": email,
                "descripcion": descripcion,
                "idioma_paciente": idioma_detectado,
                "idioma_formulario": idioma_seleccionado,
                "tiempo_padecimiento": tiempo_padecimiento,
                "frecuencia": frecuencia,
                "fecha_registro": datetime.now().isoformat(),
                "consentimiento_aceptado": True
            }
            
            st.session_state.paciente_actual = datos_paciente
            st.session_state.mostrar_diagnostico = True
            st.session_state.idioma_actual = idioma_detectado
            st.rerun()

# ================= GENERAR DIAGNÓSTICO MEJORADO =================
def generar_diagnostico_multi_idioma(sistema, datos_paciente):
    """Genera diagnóstico en el idioma del paciente."""
    
    idioma = datos_paciente.get("idioma_paciente", "es")
    
    # Mapeo de idiomas para prompts más precisos
    mapeo_idiomas_prompts = {
        "es": "ESPANOL",
        "en": "ENGLISH", 
        "pt": "PORTUGUESE",
        "fr": "FRENCH",
        "de": "GERMAN",
        "it": "ITALIAN"
    }
    
    idioma_prompt = mapeo_idiomas_prompts.get(idioma, "ESPANOL")
    
    prompt = f"""
    Eres MINDGEEKCLINIC, especialista en BIODESCODIFICACIÓN con 20 años de experiencia.
    
    DATOS DEL PACIENTE:
    - Iniciales: {datos_paciente['iniciales']}
    - Edad: {datos_paciente['edad']} años
    - Estado civil: {datos_paciente['estado_civil']}
    - Situación laboral: {datos_paciente['situacion_laboral']}
    - Tensión arterial: {datos_paciente['tension']}
    
    SÍNTOMA PRINCIPAL:
    {datos_paciente['descripcion']}
    
    CARACTERÍSTICAS:
    - Tiempo: {datos_paciente['tiempo_padecimiento']}
    - Frecuencia: {datos_paciente['frecuencia']}
    
    Genera un diagnóstico COMPLETO de biodescodificación en {idioma_prompt} con esta estructura:
    
    1. 📊 **ANÁLISIS DEL CONFLICTO EMOCIONAL**
       - Conflicto central identificado
       - Emociones asociadas
       - Posible evento desencadenante
    
    2. 🔬 **SIGNIFICADO BIOLÓGICO**
       - Qué representa el síntoma biológicamente
       - Órgano/sistema afectado
       - Función biológica alterada
    
    3. 🎯 **PROTOCOLO DE 3 SESIONES**
       - SESIÓN 1: Identificación y aceptación
       - SESIÓN 2: Reprogramación emocional  
       - SESIÓN 3: Integración y seguimiento
    
    4. 🧘 **TÉCNICAS COMPLEMENTARIAS**
       - Hipnosis/autohipnosis (instrucciones específicas)
       - Afirmaciones personalizadas
       - Ejercicios de liberación emocional
    
    5. 📈 **PRONÓSTICO Y RECOMENDACIONES**
       - Tiempo estimado de mejoría
       - Recomendaciones específicas
       - Señales de alarma
    
    Usa un tono profesional pero empático. Incluye ejemplos concretos basados en los datos del paciente.
    """
    
    try:
        logger.info(f"Generando diagnóstico para paciente {datos_paciente['iniciales']} en idioma {idioma}")
        
        # Asegurarnos de usar el método correcto
        if hasattr(sistema, 'invoke'):
            respuesta = sistema.invoke({"query": prompt})
            resultado = respuesta.get('result', 'No se pudo generar diagnóstico')
            
            # Guardar en log para diagnóstico
            logger.info(f"Diagnóstico generado exitosamente para {datos_paciente['iniciales']}")
            return resultado
            
        else:
            logger.error("Estructura del sistema no reconocida")
            return f"Error: Estructura del sistema no reconocida. Contacta al soporte."
            
    except Exception as e:
        logger.error(f"Error generando diagnóstico: {str(e)}")
        return f"⚠️ Se produjo un error al generar el diagnóstico. Por favor, intenta nuevamente.\n\nError técnico: {str(e)[:200]}"

# ================= SISTEMA PRINCIPAL MEJORADO =================
@st.cache_resource(show_spinner="🔄 Inicializando sistema de biodescodificación...")
def cargar_sistema_completo():
    """Carga el sistema RAG con biblioteca especializada."""
    
    if not GROQ_API_KEY:
        logger.error("GROQ_API_KEY no configurada")
        st.session_state.error_message = "API Key no configurada. Verifica los Secrets."
        return None
    
    textos = TEXTOS.get(st.session_state.get("idioma_actual", "es"), TEXTOS["es"])
    
    with st.spinner(textos.get("sistema_cargando", "🔄 Cargando sistema especializado...")):
        try:
            logger.info("Descargando base de conocimiento...")
            response = requests.get(ZIP_URL, stream=True, timeout=60, headers={'Cache-Control': 'no-cache'})
            
            if response.status_code != 200:
                logger.error(f"Error al descargar biblioteca. S
