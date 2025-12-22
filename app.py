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
import smtplib
import hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ================= CONFIGURACIÓN SEGURA =================
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")
ZIP_URL = "https://github.com/alkhimiya/mindgeekclinicdeployment/raw/refs/heads/main/mindgeekclinic_db.zip"

# ================= CONFIGURACIÓN EMAIL ARCHIVO CLÍNICO =================
EMAIL_ARCHIVO_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "promptandmente@gmail.com",
    "sender_password": "Enaraure25",
    "receiver_email": "promptandmente@gmail.com"
}

# ================= CONFIGURACIÓN IDIOMAS =================
IDIOMAS_DISPONIBLES = {
    "es": {"nombre": "Español", "emoji": "🇪🇸"},
    "en": {"nombre": "English", "emoji": "🇺🇸"},
    "pt": {"nombre": "Português", "emoji": "🇧🇷"},
    "fr": {"nombre": "Français", "emoji": "🇫🇷"},
    "de": {"nombre": "Deutsch", "emoji": "🇩🇪"},
    "it": {"nombre": "Italiano", "emoji": "🇮🇹"}
}

# Textos en español (completos)
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
        "form_titulo": "📋 FORMULARIO DE EVALUACIÓN CLÍNICA COMPLETO",
        "iniciales": "📝 **Iniciales del nombre**",
        "edad": "🎂 **Edad**",
        "email": "📧 **Correo electrónico**",
        "enviar": "🚀 **GENERAR DIAGNÓSTICO PROFESIONAL**",
        "email_placeholder": "ejemplo@correo.com",
        "email_help": "Para enviar el diagnóstico completo y terapias",
        "idioma_titulo": "🌍 **Idioma de preferencia**",
        "error_api_key": "❌ ERROR: Configura GROQ_API_KEY en Streamlit Secrets.",
        "tiempo_padecimiento": "⏳ **¿Desde hace cuánto tiempo tiene el padecimiento?**",
        "eventos_emocionales": "⚡ **Eventos emocionales que desencadenan la dolencia**",
        "eventos_placeholder": "Ej: Discusiones familiares, presión laboral, recuerdos traumáticos, situaciones de estrés específicas...",
        "estado_civil": "💍 **Estado civil**",
        "situacion_laboral": "💼 **Situación laboral**",
        "tension_alta": "🩺 **Tensión arterial alta (sistólica)**",
        "tension_baja": "🩺 **Tensión arterial baja (diastólica)**",
        "entorno_social": "👥 **Entorno social y familiar**",
        "entorno_placeholder": "Describa su entorno familiar, amistades, relaciones significativas...",
        "dolencia_principal": "🤒 **Dolencia o síntoma principal**",
        "dolencia_placeholder": "Describa detalladamente su dolencia, síntomas, localización, intensidad...",
        "frecuencia": "🔄 **Frecuencia del padecimiento**",
        "diagnostico_titulo": "🔬 **DIAGNÓSTICO PROFESIONAL DE BIODESCODIFICACIÓN**",
        "protocolo_titulo": "🗓️ **PROTOCOLO TERAPÉUTICO DE 4 SESIONES**",
        "hipnosis_titulo": "🧘 **PROTOCOLO DE HIPNOSIS (3 veces por semana)**",
        "autohipnosis_titulo": "🎵 **PROTOCOLO DE AUTOHIPNOSIS**",
        "archivo_exitoso": "📧 **Historia clínica archivada en el correo profesional**"
    }
}

# ================= FUNCIONES ESENCIALES =================
def generar_id_seguro(datos):
    """Genera ID seguro para el paciente."""
    cadena = f"{datos['iniciales']}{datos['edad']}{datos.get('email','')}{datetime.now().timestamp()}"
    return hashlib.sha256(cadena.encode()).hexdigest()[:16]

def detectar_idioma_texto(texto):
    """Detecta el idioma del texto."""
    if not texto: return "es"
    
    es_words = ['el', 'la', 'de', 'que', 'y', 'en', 'los', 'las']
    en_words = ['the', 'and', 'of', 'to', 'in', 'is', 'you', 'that']
    
    texto_lower = texto.lower()
    es_count = sum(1 for word in es_words if word in texto_lower)
    en_count = sum(1 for word in en_words if word in texto_lower)
    
    return "es" if es_count > en_count else "en"

def enviar_historia_clinica_email(datos_paciente, diagnostico, protocolo, hipnosis):
    """Envía la historia clínica completa al correo profesional."""
    try:
        server = smtplib.SMTP(EMAIL_ARCHIVO_CONFIG["smtp_server"], EMAIL_ARCHIVO_CONFIG["smtp_port"])
        server.starttls()
        server.login(EMAIL_ARCHIVO_CONFIG["sender_email"], EMAIL_ARCHIVO_CONFIG["sender_password"])
        
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ARCHIVO_CONFIG["sender_email"]
        msg['To'] = EMAIL_ARCHIVO_CONFIG["receiver_email"]
        msg['Subject'] = f"🏥 HISTORIA CLÍNICA - {datos_paciente['iniciales']} - {datetime.now().strftime('%d/%m/%Y')}"
        
        cuerpo = f"""
        MINDGEEKCLINIC - HISTORIA CLÍNICA PROFESIONAL
        {'='*60}
        
        📋 DATOS DEL PACIENTE
        {'-'*60}
        • ID: {datos_paciente['id_seguro']}
        • Iniciales: {datos_paciente['iniciales']}
        • Edad: {datos_paciente['edad']} años
        • Estado civil: {datos_paciente['estado_civil']}
        • Situación laboral: {datos_paciente['situacion_laboral']}
        • Tensión: {datos_paciente['tension']}
        • Tiempo padecimiento: {datos_paciente['tiempo_padecimiento']}
        • Frecuencia: {datos_paciente['frecuencia']}
        • Email: {datos_paciente['email']}
        
        👥 ENTORNO SOCIAL
        {'-'*60}
        {datos_paciente['entorno_social']}
        
        🤒 DOLENCIA PRINCIPAL
        {'-'*60}
        {datos_paciente['dolencia_principal']}
        
        ⚡ EVENTOS DESENCADENANTES
        {'-'*60}
        {datos_paciente['eventos_emocionales']}
        
        🧠 DIAGNÓSTICO DE BIODESCODIFICACIÓN
        {'='*60}
        
        {diagnostico}
        
        🗓️ PROTOCOLO DE 4 SESIONES
        {'='*60}
        
        {protocolo}
        
        🧘 PROTOCOLO DE HIPNOSIS
        {'='*60}
        
        {hipnosis}
        
        🔒 ARCHIVO CLÍNICO
        {'-'*60}
        • Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
        • Sistema: MINDGEEKCLINIC v9.0
        • Profesional: promptandmente@gmail.com
        """
        
        msg.attach(MIMEText(cuerpo, 'plain'))
        server.send_message(msg)
        server.quit()
        return True, "✅ Historia clínica archivada correctamente."
    except Exception as e:
        return False, f"❌ Error al archivar: {str(e)}"

# ================= FORMULARIO CLÍNICO COMPLETO =================
def mostrar_consentimiento():
    textos = TEXTOS["es"]
    with st.expander(f"📄 {textos['consentimiento_titulo']}", expanded=True):
        st.markdown(textos['consentimiento_texto'])
        aceptado = st.checkbox(textos['acepto'], key="consentimiento")
        return aceptado

def formulario_diagnostico_completo():
    textos = TEXTOS["es"]
    
    st.markdown(f"### {textos['form_titulo']}")
    
    with st.form("formulario_clinico_profesional"):
        # Consentimiento (OBLIGATORIO)
        if not mostrar_consentimiento():
            st.error("❌ Debe aceptar el consentimiento informado para continuar.")
            st.stop()
        
        st.markdown("---")
        
        # ========== SECCIÓN 1: DATOS PERSONALES ==========
        st.markdown("#### 📊 **DATOS PERSONALES**")
        col1, col2 = st.columns(2)
        
        with col1:
            iniciales = st.text_input(
                textos['iniciales'],
                max_chars=3,
                help="Ej: JPG para Juan Pérez García"
            )
            edad = st.number_input(
                textos['edad'],
                min_value=1,
                max_value=120,
                value=30
            )
            estado_civil = st.selectbox(
                textos['estado_civil'],
                ["Soltero", "Casado", "Divorciado", "Viudo", "Unión libre", "Separado"]
            )
            
        with col2:
            situacion_laboral = st.selectbox(
                textos['situacion_laboral'],
                ["Empleado", "Desempleado", "Independiente", "Estudiante", "Jubilado", "Incapacitado"]
            )
            tension_alta = st.number_input(
                textos['tension_alta'],
                min_value=50,
                max_value=250,
                value=120
            )
            tension_baja = st.number_input(
                textos['tension_baja'],
                min_value=30,
                max_value=150,
                value=80
            )
        
        # Email
        email = st.text_input(
            textos['email'],
            placeholder=textos['email_placeholder'],
            help=textos['email_help']
        )
        
        # ========== SECCIÓN 2: TIEMPO Y FRECUENCIA ==========
        st.markdown("---")
        st.markdown("#### ⏳ **TIEMPO Y FRECUENCIA**")
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            tiempo_padecimiento = st.selectbox(
                textos['tiempo_padecimiento'],
                ["Menos de 1 mes", "1-3 meses", "3-6 meses", "6-12 meses", "1-2 años", "2-5 años", "Más de 5 años"]
            )
        
        with col_t2:
            frecuencia = st.selectbox(
                textos['frecuencia'],
                ["Constante", "Diariamente", "Varias veces por semana", "Semanalmente", "Mensualmente", "Ocasionalmente"]
            )
        
        # ========== SECCIÓN 3: ENTORNO SOCIAL ==========
        st.markdown("---")
        st.markdown("#### 👥 **ENTORNO SOCIAL Y FAMILIAR**")
        entorno_social = st.text_area(
            textos['entorno_social'],
            height=80,
            placeholder=textos['entorno_placeholder']
        )
        
        # ========== SECCIÓN 4: DOLENCIA PRINCIPAL ==========
        st.markdown("---")
        st.markdown("#### 🤒 **DOLENCIA O SÍNTOMA PRINCIPAL**")
        dolencia_principal = st.text_area(
            textos['dolencia_principal'],
            height=120,
            placeholder=textos['dolencia_placeholder']
        )
        
        # ========== SECCIÓN 5: EVENTOS EMOCIONALES ==========
        st.markdown("---")
        st.markdown("#### ⚡ **EVENTOS EMOCIONALES DESENCADENANTES**")
        eventos_emocionales = st.text_area(
            textos['eventos_emocionales'],
            height=100,
            placeholder=textos['eventos_placeholder'],
            help="Describa qué situaciones emocionales específicas coinciden con la aparición o empeoramiento de los síntomas"
        )
        
        # ========== SUBMIT ==========
        submitted = st.form_submit_button(
            textos['enviar'],
            type="primary",
            use_container_width=True
        )
        
        if submitted:
            if not iniciales or len(iniciales.strip()) < 2:
                st.error("❌ Iniciales requeridas (mínimo 2 caracteres)")
                return
            
            if not email or "@" not in email:
                st.error("❌ Email válido requerido para el diagnóstico profesional")
                return
            
            # Crear datos completos del paciente
            datos_paciente = {
                "id_seguro": generar_id_seguro({"iniciales": iniciales, "edad": edad, "email": email}),
                "iniciales": iniciales.upper(),
                "edad": edad,
                "estado_civil": estado_civil,
                "situacion_laboral": situacion_laboral,
                "tension": f"{tension_alta}/{tension_baja}",
                "email": email,
                "entorno_social": entorno_social,
                "dolencia_principal": dolencia_principal,
                "eventos_emocionales": eventos_emocionales,
                "tiempo_padecimiento": tiempo_padecimiento,
                "frecuencia": frecuencia,
                "fecha_registro": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "consentimiento_aceptado": True
            }
            
            # Guardar en historial
            if "pacientes" not in st.session_state:
                st.session_state.pacientes = []
            st.session_state.pacientes.append(datos_paciente)
            
            st.session_state.paciente_actual = datos_paciente
            st.session_state.mostrar_diagnostico = True
            st.rerun()

# ================= GENERAR DIAGNÓSTICO PROFESIONAL =================
def generar_diagnostico_profesional(sistema, datos_paciente):
    """Genera diagnóstico COMPLETO de biodescodificación con todos los elementos clínicos."""
    
    prompt = f"""
    ## 🧠 DIAGNÓSTICO PROFESIONAL DE BIODESCODIFICACIÓN - MINDGEEKCLINIC
    
    **DATOS COMPLETOS DEL PACIENTE:**
    - Iniciales: {datos_paciente['iniciales']}
    - Edad: {datos_paciente['edad']} años
    - Estado civil: {datos_paciente['estado_civil']}
    - Situación laboral: {datos_paciente['situacion_laboral']}
    - Tensión arterial: {datos_paciente['tension']}
    
    **CARACTERÍSTICAS TEMPORALES:**
    - Tiempo del padecimiento: {datos_paciente['tiempo_padecimiento']}
    - Frecuencia: {datos_paciente['frecuencia']}
    
    **CONTEXTO EMOCIONAL:**
    - Entorno social/familiar: {datos_paciente['entorno_social']}
    - Eventos emocionales desencadenantes: {datos_paciente['eventos_emocionales']}
    
    **DOLENCIA PRINCIPAL:**
    {datos_paciente['dolencia_principal']}
    
    **INSTRUCCIONES PARA EL ASISTENTE ESPECIALIZADO EN BIODESCODIFICACIÓN:**
    
    1. **DIAGNÓSTICO COMPLETO DE BIODESCODIFICACIÓN:**
       - Analizar la dolencia desde la perspectiva de la biodescodificación
       - Identificar el conflicto emocional específico y su relación con los eventos reportados
       - Explicar el significado biológico preciso del síntoma
       - Relacionar con los datos personales y temporales del paciente
    
    2. **PROTOCOLO TERAPÉUTICO DE 4 SESIONES (ESPECÍFICO):**
       - SESIÓN 1: Identificación del conflicto y aceptación
       - SESIÓN 2: Reprogramación emocional específica
       - SESIÓN 3: Integración y nuevas estrategias
       - SESIÓN 4: Cierre y seguimiento
    
    3. **PROTOCOLO DE HIPNOSIS (PARA TERAPEUTA):**
       - Frecuencia: 3 veces por semana (específico)
       - Duración por sesión: 15-20 minutos
       - Técnicas específicas basadas en el diagnóstico
       - Instrucciones paso a paso para el terapeuta
    
    4. **PROTOCOLO DE AUTOHIPNOSIS (PARA PACIENTE):**
       - Instrucciones para grabación personal
       - Frecuencia: 3 veces por semana
       - Duración: 12-15 minutos por sesión
       - Afirmaciones específicas basadas en el conflicto identificado
    
    5. **RECOMENDACIONES COMPLEMENTARIAS:**
       - Ejercicios emocionales diarios
       - Actividades específicas de integración
       - Señales de alarma a observar
    
    **GENERAR RESPUESTA ESTRUCTURADA EN ESPAÑOL CON:**
    1. 🧠 DIAGNÓSTICO DE BIODESCODIFICACIÓN (completo)
    2. 🗓️ PROTOCOLO DE 4 SESIONES (detallado)
    3. 🧘 PROTOCOLO DE HIPNOSIS (para terapeuta)
    4. 🎵 PROTOCOLO DE AUTOHIPNOSIS (para paciente)
    5. 💡 RECOMENDACIONES ESPECÍFICAS
    
    **RESPUESTA PROFESIONAL Y ESPECÍFICA:**
    """
    
    try:
        respuesta = sistema.invoke({"query": prompt})
        return respuesta['result']
    except Exception as e:
        return f"Error al generar diagnóstico profesional: {str(e)}"

# ================= SISTEMA RAG =================
@st.cache_resource
def cargar_sistema_completo():
    if not GROQ_API_KEY:
        st.error(TEXTOS["es"]["error_api_key"])
        return None
    
    with st.spinner("🔄 Cargando sistema especializado en biodescodificación..."):
        try:
            response = requests.get(ZIP_URL, stream=True, timeout=60)
            if response.status_code != 200:
                st.error("❌ Error al descargar biblioteca especializada.")
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
                max_tokens=4000
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
            st.error(f"❌ Error crítico: {str(e)[:150]}")
            return None

# ================= INTERFAZ PRINCIPAL =================
st.set_page_config(
    page_title="MINDGEEKCLINIC - Sistema Profesional de Biodescodificación",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar profesional
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/271/271226.png", width=80)
    st.markdown("### 🏥 MINDGEEKCLINIC")
    st.markdown("**Sistema Profesional con Protocolos Clínicos**")
    st.markdown("---")
    
    st.markdown("#### 📊 Estadísticas Clínicas")
    if "pacientes" in st.session_state:
        st.metric("Historias clínicas", len(st.session_state.pacientes))
    
    st.markdown("---")
    
    if st.button("🆕 Nueva Evaluación", use_container_width=True, type="primary"):
        for key in ["mostrar_diagnostico", "paciente_actual", "diagnostico_completo"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    
    st.markdown("---")
    st.caption("🔒 Archivo profesional en promptandmente@gmail.com")

# Inicializar estados
if "mostrar_diagnostico" not in st.session_state:
    st.session_state.mostrar_diagnostico = False

# Título principal
st.title("🧠 MINDGEEKCLINIC")
st.markdown("### **Sistema Profesional de Diagnóstico por Biodescodificación**")
st.markdown("*Protocolos clínicos completos para profesionales de salud mental*")
st.markdown("---")

# Cargar sistema
sistema = cargar_sistema_completo()

if not sistema:
    st.error("⚠️ Sistema no disponible. Verifica la configuración de GROQ_API_KEY en Secrets.")
    st.stop()

# Mostrar formulario o diagnóstico
if not st.session_state.mostrar_diagnostico:
    formulario_diagnostico_completo()
else:
    paciente = st.session_state.paciente_actual
    
    # Mostrar datos del paciente
    st.markdown(f"### 📄 **PACIENTE:** {paciente['iniciales']} • {paciente['edad']} años • {paciente['estado_civil']}")
    
    with st.expander("📋 Ver datos clínicos completos"):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Situación laboral:** {paciente['situacion_laboral']}")
            st.write(f"**Tensión arterial:** {paciente['tension']}")
            st.write(f"**Tiempo padecimiento:** {paciente['tiempo_padecimiento']}")
        with col2:
            st.write(f"**Frecuencia:** {paciente['frecuencia']}")
            st.write(f"**ID Seguro:** `{paciente['id_seguro']}`")
            st.write(f"**Email:** {paciente['email']}")
    
    # Generar diagnóstico profesional
    st.markdown("---")
    st.markdown("### 🔬 **DIAGNÓSTICO PROFESIONAL DE BIODESCODIFICACIÓN**")
    
    if "diagnostico_completo" not in st.session_state:
        with st.spinner("🔄 Generando diagnóstico profesional con protocolos clínicos..."):
            diagnostico_completo = generar_diagnostico_profesional(sistema, paciente)
            st.session_state.diagnostico_completo = diagnostico_completo
    
    # Mostrar diagnóstico completo
    st.markdown(st.session_state.diagnostico_completo)
    
    # ========== ARCHIVO CLÍNICO PROFESIONAL ==========
    st.markdown("---")
    st.markdown("### 📧 **ARCHIVO CLÍNICO PROFESIONAL**")
    
    if st.button("📁 Archivar Historia Clínica Completa", use_container_width=True, type="primary"):
        with st.spinner("📨 Enviando al correo profesional..."):
            # Separar las secciones del diagnóstico
            diagnostico_texto = st.session_state.diagnostico_completo
            
            exito, mensaje = enviar_historia_clinica_email(
                paciente, 
                diagnostico_texto,
                "Protocolo de 4 sesiones incluido en el diagnóstico",
                "Protocolos de hipnosis y autohipnosis incluidos"
            )
            
            if exito:
                st.success(mensaje)
                st.info(f"📂 Revisa tu correo profesional: **promptandmente@gmail.com**")
            else:
                st.error(mensaje)
    
    # ========== PROTOCOLOS ESPECÍFICOS ==========
    st.markdown("---")
    st.markdown("### 🗓️ **PROTOCOLOS TERAPÉUTICOS ESPECÍFICOS**")
    
    col_p1, col_p2 = st.columns(2)
    
    with col_p1:
        st.markdown("#### 🧘 **PROTOCOLO DE HIPNOSIS**")
        st.info("""
        **Para aplicación por terapeuta:**
        - Frecuencia: **3 veces por semana** (específico)
        - Duración: 15-20 minutos por sesión
        - Técnicas específicas basadas en el diagnóstico
        - Instrucciones detalladas para el terapeuta
        
        **Recomendaciones:**
        1. Sesión guiada de identificación
        2. Técnicas de regresión emocional
        3. Reprogramación específica
        4. Integración y cierre
        """)
    
    with col_p2:
        st.markdown("#### 🎵 **PROTOCOLO DE AUTOHIPNOSIS**")
        st.info("""
        **Para el paciente (grabación):**
        - Frecuencia: **3 veces por semana**
        - Duración: 12-15 minutos
        - Ambiente tranquilo y posición cómoda
        
        **Instrucciones grabación:**
        1. Grabar en dispositivo de audio
        2. Incluir instrucciones respiratorias
        3. Afirmaciones personalizadas
        4. Guía paso a paso
        
        **Seguimiento:** Registrar efectos después de cada sesión
        """)
    
    # ========== NUEVA EVALUACIÓN ==========
    st.markdown("---")
    if st.button("🆕 Realizar Nueva Evaluación Clínica", use_container_width=True, type="primary"):
        for key in ["mostrar_diagnostico", "paciente_actual", "diagnostico_completo"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# Footer profesional
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.8em;'>
    🧠 <b>MINDGEEKCLINIC v9.0</b> • Sistema profesional completo • 
    Protocolos de 4 sesiones • Hipnosis 3 veces/semana • Archivo en promptandmente@gmail.com
    </div>
    """,
    unsafe_allow_html=True
)
