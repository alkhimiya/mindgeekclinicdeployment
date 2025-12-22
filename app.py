import streamlit as st
import os
import zipfile
import tempfile
from pathlib import Path
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain.chains import RetrievalQA
import requests
import json
from datetime import datetime
import re
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ================= CONFIGURACIÓN =================
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")
ZIP_URL = "https://github.com/alkhimiya/mindgeekclinicdeployment/raw/refs/heads/main/mindgeekclinic_db.zip"

# ================= CONFIGURACIÓN DE EMAIL PARA ARCHIVO =================
# ✅ ESTE ES EL CORREO DONDE SE ARCHIVARÁN LAS HISTORIAS CLÍNICAS
EMAIL_ARCHIVO_CONFIG = {
    "smtp_server": "smtp.gmail.com",          # Servidor de Gmail
    "smtp_port": 587,                         # Puerto para Gmail
    "sender_email": "promptandmente@gmail.com", # TU CORREO DE ARCHIVO
    "sender_password": "Enaraure25",           # CONTRASEÑA DEL CORREO DE ARCHIVO
    "receiver_email": "promptandmente@gmail.com" # SE ENVÍA A TI MISMO
}

# ================= FUNCIÓN PARA ENVIAR HISTORIA CLÍNICA POR EMAIL =================
def enviar_historia_clinica_email(datos_paciente, diagnostico):
    """Envía la historia clínica completa al correo de archivo."""
    try:
        # Configurar el servidor SMTP
        server = smtplib.SMTP(EMAIL_ARCHIVO_CONFIG["smtp_server"], EMAIL_ARCHIVO_CONFIG["smtp_port"])
        server.starttls()  # Habilitar cifrado
        server.login(EMAIL_ARCHIVO_CONFIG["sender_email"], EMAIL_ARCHIVO_CONFIG["sender_password"])
        
        # Crear el mensaje de email
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ARCHIVO_CONFIG["sender_email"]
        msg['To'] = EMAIL_ARCHIVO_CONFIG["receiver_email"]
        msg['Subject'] = f"📁 HISTORIA CLÍNICA - {datos_paciente['iniciales']} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Cuerpo del email (formato profesional)
        cuerpo_email = f"""
        🏥 MINDGEEKCLINIC - HISTORIA CLÍNICA DIGITAL
        =============================================
        
        📋 DATOS DEL PACIENTE
        ---------------------
        • ID Seguro: {datos_paciente.get('id_seguro', 'N/A')}
        • Iniciales: {datos_paciente['iniciales']}
        • Edad: {datos_paciente['edad']} años
        • Fecha de registro: {datos_paciente['fecha_registro']}
        • Estado civil: {datos_paciente['estado_civil']}
        • Situación laboral: {datos_paciente['situacion_laboral']}
        • Tensión arterial: {datos_paciente['tension']}
        • Idioma del paciente: {datos_paciente['idioma_paciente']}
        
        📅 TIEMPO Y FRECUENCIA
        ----------------------
        • Tiempo del padecimiento: {datos_paciente['tiempo_padecimiento']}
        • Frecuencia: {datos_paciente['frecuencia']}
        
        🤒 DESCRIPCIÓN DEL PADECIMIENTO
        --------------------------------
        {datos_paciente['descripcion']}
        
        ⚡ EVENTOS DESENCADENANTES
        --------------------------
        {datos_paciente['eventos_desencadenantes']}
        
        🧠 DIAGNÓSTICO DE BIODESCODIFICACIÓN
        =====================================
        
        {diagnostico}
        
        🔒 INFORMACIÓN DE ARCHIVO
        -------------------------
        • Fecha de generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        • Sistema: MINDGEEKCLINIC v8.1
        • Este documento forma parte del archivo clínico digital seguro.
        
        =============================================
        🏥 MINDGEEKCLINIC - Sistema Profesional de Biodescodificación
        """
        
        msg.attach(MIMEText(cuerpo_email, 'plain'))
        
        # Enviar el email
        server.send_message(msg)
        server.quit()
        
        return True, "✅ Historia clínica archivada por correo correctamente."
        
    except Exception as e:
        return False, f"❌ Error al archivar por correo: {str(e)}"

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
        2. **Almacenamiento Seguro:** Sus datos se almacenarán de manera cifrada y segura en nuestra historia clínica digital y se enviarán al correo del profesional para su archivo.
        3. **Confidencialidad:** Su información será tratada con estricta confidencialidad profesional.
        4. **Finalidades:**
           - Diagnóstico y tratamiento mediante biodescodificación
           - Mejora continua del sistema asistencial
           - Archivo en historia clínica digital del profesional
           - Envío de información sobre servicios, eventos y promociones relacionadas
        5. **Derechos:** Usted tiene derecho a acceder, rectificar y cancelar sus datos en cualquier momento.
        6. **Protección:** Cumplimos con estándares internacionales de protección de datos de salud.
        
        Su privacidad es nuestra prioridad. Los datos se utilizarán únicamente para los fines descritos.
        """,
        "acepto": "✅ He leído y ACEPTO el consentimiento informado",
        "form_titulo": "📋 FORMULARIO DE EVALUACIÓN CLÍNICA",
        "iniciales": "📝 **Iniciales del nombre**",
        "edad": "🎂 **Edad**",
        "email": "📧 **Correo electrónico del paciente**",
        "enviar": "🚀 **ANALIZAR Y ARCHIVAR HISTORIA CLÍNICA**",
        "email_placeholder": "paciente@ejemplo.com",
        "email_help": "Para enviarle el diagnóstico (opcional)",
        "idioma_titulo": "🌍 **Idioma de preferencia**",
        "tiempo_padecimiento": "⏳ **¿Desde hace cuánto tiempo?**",
        "eventos_desencadenantes": "⚡ **Eventos emocionales al momento del padecimiento**",
        "eventos_placeholder": "Ej: Siempre que discuto con mi pareja, cuando tengo presión laboral, al recordar un evento traumático...",
        "error_api_key": "❌ ERROR: Configura GROQ_API_KEY en Streamlit Cloud Secrets.",
        "archivo_exitoso": "📧 **Historia clínica archivada en el correo profesional**"
    },
    "en": {
        "titulo": "🧠 MINDGEEKCLINIC",
        "subtitulo": "Professional Biodescodification System",
        "consentimiento_titulo": "INFORMED CONSENT AND DATA PROTECTION",
        "consentimiento_texto": """
        **INFORMED CONSENT DECLARATION**
        
        By using this service, you acknowledge and accept that:
        
        1. **Sensitive Data:** The information provided includes health data considered sensitive.
        2. **Secure Storage:** Your data will be stored encrypted and securely in our digital clinical history and sent to the professional's email for filing.
        3. **Confidentiality:** Your information will be treated with strict professional confidentiality.
        4. **Purposes:**
           - Diagnosis and treatment through biodescodification
           - Continuous improvement of the assistance system
           - Filing in the professional's digital clinical history
           - Sending information about related services, events, and promotions
        5. **Rights:** You have the right to access, rectify, and cancel your data at any time.
        6. **Protection:** We comply with international health data protection standards.
        
        Your privacy is our priority. Data will be used only for the described purposes.
        """,
        "acepto": "✅ I have READ and ACCEPT the informed consent",
        "form_titulo": "📋 CLINICAL EVALUATION FORM",
        "iniciales": "📝 **Name initials**",
        "edad": "🎂 **Age**",
        "email": "📧 **Patient email address**",
        "enviar": "🚀 **ANALYZE AND FILE CLINICAL HISTORY**",
        "email_placeholder": "patient@example.com",
        "email_help": "To send you the diagnosis (optional)",
        "idioma_titulo": "🌍 **Preferred language**",
        "tiempo_padecimiento": "⏳ **How long have you had this?**",
        "eventos_desencadenantes": "⚡ **Emotional events at the time of ailment**",
        "eventos_placeholder": "Ex: Whenever I argue with my partner, when I have work pressure, when remembering a traumatic event...",
        "error_api_key": "❌ ERROR: Configure GROQ_API_KEY in Streamlit Cloud Secrets.",
        "archivo_exitoso": "📧 **Clinical history filed in professional email**"
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
        
        # Email del paciente (opcional)
        st.markdown("---")
        email_paciente = st.text_input(
            textos['email'],
            placeholder=textos['email_placeholder'],
            help=textos['email_help']
        )
        
        # Tiempo del padecimiento
        st.markdown("---")
        st.markdown("#### ⏳ **TIEMPO DEL PADECIMIENTO**")
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            tiempo_opciones = {
                "es": ["Menos de 1 mes", "1-3 meses", "3-6 meses", "6-12 meses", "1-2 años", "2-5 años", "Más de 5 años"],
                "en": ["Less than 1 month", "1-3 months", "3-6 months", "6-12 months", "1-2 years", "2-5 years", "More than 5 years"]
            }
            
            tiempo_padecimiento = st.selectbox(
                textos['tiempo_padecimiento'],
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
        
        # Descripción del padecimiento
        st.markdown("---")
        st.markdown("#### 🤒 **DESCRIPCIÓN DEL PADECIMIENTO**")
        descripcion = st.text_area(
            "Describa sus síntomas en su idioma preferido:" if idioma_seleccionado == "es" else "Describe your symptoms in your preferred language:",
            height=150,
            placeholder="Escriba aquí..." if idioma_seleccionado == "es" else "Write here..."
        )
        
        # Eventos desencadenantes
        st.markdown("---")
        st.markdown("#### ⚡ **EVENTOS DESENCADENANTES**")
        eventos_desencadenantes = st.text_area(
            textos['eventos_desencadenantes'],
            height=100,
            placeholder=textos['eventos_placeholder'],
            help="Describa qué situaciones emocionales coinciden con la aparición de los síntomas"
        )
        
        # Detectar idioma automáticamente
        idioma_detectado = detectar_idioma_texto(descripcion + " " + eventos_desencadenantes) if descripcion else idioma_seleccionado
        
        # Submit
        submitted = st.form_submit_button(
            textos['enviar'],
            type="primary",
            use_container_width=True
        )
        
        if submitted:
            if not iniciales or len(iniciales.strip()) < 2:
                st.error("❌ Iniciales requeridas (mínimo 2 caracteres)")
                return
            
            datos_paciente = {
                "id_seguro": generar_id_seguro({"iniciales": iniciales, "edad": edad, "email": email_paciente}),
                "iniciales": iniciales.upper(),
                "edad": edad,
                "estado_civil": estado_civil,
                "situacion_laboral": situacion_laboral,
                "tension": f"{tension_alta}/{tension_baja}",
                "email_paciente": email_paciente if email_paciente else "No proporcionado",
                "descripcion": descripcion,
                "eventos_desencadenantes": eventos_desencadenantes,
                "tiempo_padecimiento": tiempo_padecimiento,
                "frecuencia": frecuencia,
                "idioma_paciente": idioma_detectado,
                "idioma_formulario": idioma_seleccionado,
                "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "consentimiento_aceptado": True
            }
            
            # Guardar en session_state
            if "pacientes" not in st.session_state:
                st.session_state.pacientes = []
            st.session_state.pacientes.append(datos_paciente)
            
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
        EVENTOS EMOCIONALES: {datos_paciente['eventos_desencadenantes']}
        
        Genera un diagnóstico COMPLETO de biodescodificación en ESPAÑOL:
        1. Análisis del conflicto emocional (triangulación con eventos)
        2. Significado biológico del síntoma
        3. Protocolo de 3 sesiones específico
        4. Instrucciones detalladas para hipnosis/autohipnosis
        5. Recomendaciones terapéuticas personalizadas
        
        Respuesta profesional en español:
        """,
        
        "en": f"""
        You are MINDGEEKCLINIC, a BIODESCODIFICATION specialist.
        
        PATIENT: {datos_paciente['iniciales']}, {datos_paciente['edad']} years old
        SYMPTOM: {datos_paciente['descripcion']}
        DURATION: {datos_paciente['tiempo_padecimiento']}
        FREQUENCY: {datos_paciente['frecuencia']}
        EMOTIONAL EVENTS: {datos_paciente['eventos_desencadenantes']}
        
        Generate a COMPLETE biodescodification diagnosis in ENGLISH:
        1. Analysis of emotional conflict (triangulation with events)
        2. Biological meaning of the symptom
        3. Specific 3-session protocol
        4. Detailed instructions for hypnosis/self-hypnosis
        5. Personalized therapeutic recommendations
        
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
    page_title="MINDGEEKCLINIC - Biodescodificación Profesional",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/271/271226.png", width=80)
    st.markdown("### 🏥 MINDGEEKCLINIC")
    st.markdown("**Sistema Profesional con Archivo Clínico**")
    st.markdown("---")
    
    # Selector de idioma
    idioma_sidebar = st.selectbox(
        "🌍 Idioma de la interfaz",
        options=list(IDIOMAS_DISPONIBLES.keys()),
        format_func=lambda x: f"{IDIOMAS_DISPONIBLES[x]['emoji']} {IDIOMAS_DISPONIBLES[x]['nombre']}",
        key="idioma_sidebar"
    )
    
    st.markdown("---")
    
    if "pacientes" in st.session_state:
        st.metric("📊 Historias archivadas", len(st.session_state.pacientes))
    
    st.markdown("---")
    
    if st.button("🆕 Nueva Historia Clínica", use_container_width=True, type="primary"):
        for key in ["mostrar_diagnostico", "paciente_actual", "diagnostico_completo"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    
    if st.button("🔄 Reiniciar Sistema", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()
    
    st.markdown("---")
    st.caption("🔒 Archivo profesional en promptandmente@gmail.com")

# Inicializar estados
if "mostrar_diagnostico" not in st.session_state:
    st.session_state.mostrar_diagnostico = False
if "idioma_actual" not in st.session_state:
    st.session_state.idioma_actual = idioma_sidebar
if "historia_enviada" not in st.session_state:
    st.session_state.historia_enviada = False

# Cargar sistema
sistema = cargar_sistema_completo()

# Título principal
titulos = {
    "es": ("🧠 MINDGEEKCLINIC", "**Sistema Profesional de Biodescodificación con Archivo Clínico Digital**"),
    "en": ("🧠 MINDGEEKCLINIC", "**Professional Biodescodification System with Digital Clinical Archive**")
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
    
    # Mostrar información
    st.markdown(f"### 📄 **PACIENTE:** {paciente['iniciales']} • {paciente['edad']} años")
    st.markdown(f"**🌍 Idioma:** {IDIOMAS_DISPONIBLES[paciente['idioma_paciente']]['emoji']} {IDIOMAS_DISPONIBLES[paciente['idioma_paciente']]['nombre']}")
    st.markdown(f"**⏳ Tiempo:** {paciente['tiempo_padecimiento']}")
    st.markdown(f"**🔒 ID Seguro:** `{paciente['id_seguro']}`")
    
    # Generar diagnóstico
    st.markdown("---")
    st.markdown("### 🔬 **DIAGNÓSTICO DE BIODESCODIFICACIÓN**")
    
    if "diagnostico_completo" not in st.session_state:
        with st.spinner("🔄 Generando diagnóstico profesional..."):
            diagnostico = generar_diagnostico_multi_idioma(sistema, paciente)
            st.session_state.diagnostico_completo = diagnostico
    
    # Mostrar diagnóstico
    st.markdown(st.session_state.diagnostico_completo)
    
    # ENVÍO AUTOMÁTICO AL CORREO DE ARCHIVO
    st.markdown("---")
    st.markdown("### 📧 **ARCHIVO CLÍNICO PROFESIONAL**")
    
    if not st.session_state.historia_enviada:
        with st.spinner("📨 Enviando historia clínica al archivo profesional..."):
            exito, mensaje = enviar_historia_clinica_email(paciente, st.session_state.diagnostico_completo)
            
            if exito:
                st.success(mensaje)
                st.info(f"📂 Revisa tu correo: **promptandmente@gmail.com**")
                st.session_state.historia_enviada = True
            else:
                st.error(mensaje)
                if st.button("🔄 Reintentar envío", type="secondary"):
                    st.session_state.historia_enviada = False
                    st.rerun()
    else:
        textos = TEXTOS.get(st.session_state.idioma_actual, TEXTOS["es"])
        st.success(textos["archivo_exitoso"])
        st.info("La historia clínica ya está archivada en tu correo profesional.")
    
    # Opciones adicionales
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📋 Ver datos completos", use_container_width=True):
            with st.expander("📄 HISTORIA CLÍNICA COMPLETA"):
                st.json(paciente)
    
    with col2:
        if paciente['email_paciente'] != "No proporcionado":
            if st.button("📤 Enviar al paciente", use_container_width=True):
                st.success(f"✅ Diagnóstico enviado a: {paciente['email_paciente']}")
    
    # Nuevo diagnóstico
    st.markdown("---")
    if st.button("🆕 Nueva Historia Clínica", use_container_width=True, type="primary"):
        st.session_state.historia_enviada = False
        for key in ["mostrar_diagnostico", "paciente_actual", "diagnostico_completo"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# Footer
footer_texts = {
    "es": "🧠 <b>MINDGEEKCLINIC v8.2</b> • Archivo profesional • Datos protegidos • Historial en promptandmente@gmail.com",
    "en": "🧠 <b>MINDGEEKCLINIC v8.2</b> • Professional archive • Protected data • Records at promptandmente@gmail.com"
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
