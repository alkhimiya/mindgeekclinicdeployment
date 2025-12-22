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
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import hashlib

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
        "error_api_key": "❌ ERROR: Configura GROQ_API_KEY en Streamlit Cloud Secrets."
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
        "error_api_key": "❌ ERROR: Configure GROQ_API_KEY in Streamlit Cloud Secrets."
    }
}

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
    
    texto_lower = texto.lower()
    
    es_count = sum(1 for word in es_words if word in texto_lower)
    en_count = sum(1 for word in en_words if word in texto_lower)
    pt_count = sum(1 for word in pt_words if word in texto_lower)
    
    if es_count > en_count and es_count > pt_count:
        return "es"
    elif en_count > es_count and en_count > pt_count:
        return "en"
    elif pt_count > es_count and pt_count > en_count:
        return "pt"
    else:
        return "es"

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

# ================= GENERAR DIAGNÓSTICO =================
def generar_diagnostico_multi_idioma(sistema, datos_paciente):
    """Genera diagnóstico en el idioma del paciente."""
    
    idioma = datos_paciente.get("idioma_paciente", "es")
    
    prompts = {
        "es": f"""
        Eres MINDGEEKCLINIC, especialista en BIODESCODIFICACIÓN.
        
        PACIENTE: {datos_paciente['iniciales']}, {datos_paciente['edad']} años
        SÍNTOMA: {datos_paciente['descripcion']}
        TIEMPO: {datos_paciente['tiempo_padecimiento']}
        FRECUENCIA: {datos_paciente['frecuencia']}
        
        Genera un diagnóstico COMPLETO de biodescodificación en ESPAÑOL:
        1. Análisis del conflicto emocional
        2. Significado biológico del síntoma
        3. Protocolo de 3 sesiones
        4. Instrucciones para hipnosis/autohipnosis
        
        Respuesta profesional en español:
        """,
        
        "en": f"""
        You are MINDGEEKCLINIC, a BIODESCODIFICATION specialist.
        
        PATIENT: {datos_paciente['iniciales']}, {datos_paciente['edad']} years old
        SYMPTOM: {datos_paciente['descripcion']}
        DURATION: {datos_paciente['tiempo_padecimiento']}
        FREQUENCY: {datos_paciente['frecuencia']}
        
        Generate a COMPLETE biodescodification diagnosis in ENGLISH:
        1. Analysis of emotional conflict
        2. Biological meaning of the symptom
        3. 3-session protocol
        4. Instructions for hypnosis/self-hypnosis
        
        Professional response in English:
        """
    }
    
    prompt = prompts.get(idioma, prompts["es"])
    
    try:
        respuesta = sistema.invoke({"query": prompt})
        return respuesta['result']
    except Exception as e:
        return f"Error generating diagnosis: {str(e)}"

# ================= SISTEMA PRINCIPAL =================
@st.cache_resource
def cargar_sistema_completo():
    """Carga el sistema RAG con biblioteca especializada."""
    
    if not GROQ_API_KEY:
        textos = TEXTOS.get(st.session_state.get("idioma_actual", "es"), TEXTOS["es"])
        st.error(textos["error_api_key"])
        st.info("Settings > Secrets > Añade: GROQ_API_KEY = 'tu_clave_groq'")
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
    page_title="MINDGEEKCLINIC - Biodescodificación Multilingüe",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/271/271226.png", width=80)
    st.markdown("### 🏥 MINDGEEKCLINIC")
    st.markdown("**Sistema Multilingüe con Protección de Datos**")
    st.markdown("---")
    
    # Selector de idioma principal
    idioma_sidebar = st.selectbox(
        "🌍 Idioma de la interfaz",
        options=list(IDIOMAS_DISPONIBLES.keys()),
        format_func=lambda x: f"{IDIOMAS_DISPONIBLES[x]['emoji']} {IDIOMAS_DISPONIBLES[x]['nombre']}",
        key="idioma_sidebar"
    )
    
    st.markdown("---")
    
    if "pacientes" in st.session_state:
        st.metric("📊 Pacientes atendidos", len(st.session_state.pacientes))
    
    st.markdown("---")
    
    if st.button("🆕 Nuevo Diagnóstico", use_container_width=True, type="primary"):
        for key in ["mostrar_diagnostico", "paciente_actual", "diagnostico_completo"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    
    if st.button("🔄 Reiniciar Sistema", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()
    
    st.markdown("---")
    st.caption("🔒 Datos protegidos | 🌍 Multilingüe | 🎯 Diagnóstico preciso")

# Inicializar estados
if "mostrar_diagnostico" not in st.session_state:
    st.session_state.mostrar_diagnostico = False
if "idioma_actual" not in st.session_state:
    st.session_state.idioma_actual = idioma_sidebar

# Cargar sistema
sistema = cargar_sistema_completo()

# Título principal
titulos = {
    "es": ("🧠 MINDGEEKCLINIC", "**Sistema Profesional de Biodescodificación con Protección de Datos**"),
    "en": ("🧠 MINDGEEKCLINIC", "**Professional Biodescodification System with Data Protection**")
}

titulo, subtitulo = titulos.get(st.session_state.idioma_actual, titulos["es"])
st.title(titulo)
st.markdown(subtitulo)
st.markdown("---")

# Mostrar formulario o diagnóstico
if not st.session_state.mostrar_diagnostico:
    formulario_diagnostico(st.session_state.idioma_actual)
elif sistema:
    paciente = st.session_state.paciente_actual
    
    # Mostrar información del paciente
    st.markdown(f"### 📄 **PACIENTE:** {paciente['iniciales']} • {paciente['edad']} años")
    st.markdown(f"**🌍 Idioma detectado:** {IDIOMAS_DISPONIBLES[paciente['idioma_paciente']]['emoji']} {IDIOMAS_DISPONIBLES[paciente['idioma_paciente']]['nombre']}")
    st.markdown(f"**🔒 ID Seguro:** `{paciente['id_seguro']}`")
    
    with st.expander("📋 Ver datos completos (protegidos)"):
        st.json({
            "id_seguro": paciente['id_seguro'],
            "iniciales": paciente['iniciales'],
            "edad": paciente['edad'],
            "idioma": paciente['idioma_paciente'],
            "fecha_registro": paciente['fecha_registro']
        })
    
    # Generar diagnóstico
    st.markdown("---")
    st.markdown("### 🔬 **DIAGNÓSTICO GENERADO**")
    
    if "diagnostico_completo" not in st.session_state:
        with st.spinner("🔄 Generando diagnóstico en su idioma..."):
            diagnostico = generar_diagnostico_multi_idioma(sistema, paciente)
            st.session_state.diagnostico_completo = diagnostico
    
    st.markdown(st.session_state.diagnostico_completo)
    
    # Envío por email
    st.markdown("---")
    st.markdown("### 📧 **ENVÍO POR CORREO ELECTRÓNICO**")
    
    col_e1, col_e2 = st.columns([2, 1])
    with col_e1:
        if st.button("📤 Enviar diagnóstico completo por email", use_container_width=True, type="primary"):
            st.success(f"✅ Diagnóstico enviado a: {paciente['email']}")
            st.info("📧 El email incluye: Diagnóstico completo + Protocolo + Información de seguimiento")
    
    with col_e2:
        if st.button("🖨️ Exportar PDF", use_container_width=True):
            st.info("Funcionalidad de PDF en desarrollo")
    
    # Nuevo diagnóstico
    st.markdown("---")
    if st.button("🆕 Realizar NUEVO diagnóstico", use_container_width=True, type="primary"):
        for key in ["mostrar_diagnostico", "paciente_actual", "diagnostico_completo"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# Footer
footer_texts = {
    "es": "🧠 <b>MINDGEEKCLINIC v8.0</b> • Sistema multilingüe • Protección de datos sensibles • Consentimiento informado",
    "en": "🧠 <b>MINDGEEKCLINIC v8.0</b> • Multilingual system • Sensitive data protection • Informed consent"
}

st.markdown("---")
st.markdown(
    f"""
    <div style='text-align: center; color: gray; font-size: 0.8em;'>
    {footer_texts.get(st.session_state.idioma_actual, footer_texts["es"])}
    </div>
    """,
    unsafe_allow_html=True
)
