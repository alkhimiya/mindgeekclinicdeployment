import streamlit as st
import os
import zipfile
import tempfile
from pathlib import Path
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
import requests
import json
from datetime import datetime
import re
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ================= IMPORTACIÓN SEGURA DE LANGCHAIN =================
try:
    from langchain.chains import RetrievalQA
    st.success("✅ langchain.chains cargado correctamente")
except ImportError:
    st.error("❌ Error: langchain.chains no está instalado")
    st.info("""
    Instala la versión correcta ejecutando:
    ```
    pip install langchain==0.1.20
    ```
    """)
    st.stop()

# ================= CONFIGURACIÓN =================
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")
ZIP_URL = "https://github.com/alkhimiya/mindgeekclinicdeployment/raw/refs/heads/main/mindgeekclinic_db.zip"

# ================= CONFIGURACIÓN DE EMAIL PARA ARCHIVO =================
EMAIL_ARCHIVO_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "promptandmente@gmail.com",
    "sender_password": "Enaraure25",
    "receiver_email": "promptandmente@gmail.com"
}

# ================= FUNCIÓN PARA ENVIAR HISTORIA CLÍNICA =================
def enviar_historia_clinica_email(datos_paciente, diagnostico):
    """Envía la historia clínica completa al correo de archivo."""
    try:
        server = smtplib.SMTP(EMAIL_ARCHIVO_CONFIG["smtp_server"], EMAIL_ARCHIVO_CONFIG["smtp_port"])
        server.starttls()
        server.login(EMAIL_ARCHIVO_CONFIG["sender_email"], EMAIL_ARCHIVO_CONFIG["sender_password"])
        
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ARCHIVO_CONFIG["sender_email"]
        msg['To'] = EMAIL_ARCHIVO_CONFIG["receiver_email"]
        msg['Subject'] = f"📁 HISTORIA CLÍNICA - {datos_paciente['iniciales']} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        cuerpo_email = f"""
        🏥 MINDGEEKCLINIC - HISTORIA CLÍNICA DIGITAL
        =============================================
        
        📋 DATOS DEL PACIENTE
        ---------------------
        • ID Seguro: {datos_paciente.get('id_seguro', 'N/A')}
        • Iniciales: {datos_paciente['iniciales']}
        • Edad: {datos_paciente['edad']} años
        • Fecha: {datos_paciente.get('fecha_registro', 'N/A')}
        • Estado civil: {datos_paciente['estado_civil']}
        • Situación laboral: {datos_paciente['situacion_laboral']}
        • Tensión: {datos_paciente['tension']}
        
        📅 TIEMPO Y FRECUENCIA
        ----------------------
        • Tiempo: {datos_paciente['tiempo_padecimiento']}
        • Frecuencia: {datos_paciente['frecuencia']}
        
        🤒 SÍNTOMAS
        ------------
        {datos_paciente['descripcion']}
        
        ⚡ EVENTOS EMOCIONALES
        ----------------------
        {datos_paciente['eventos_desencadenantes']}
        
        🧠 DIAGNÓSTICO
        ==============
        
        {diagnostico}
        
        🔒 ARCHIVO CLÍNICO
        ------------------
        • Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        • Sistema: MINDGEEKCLINIC v8.2
        """
        
        msg.attach(MIMEText(cuerpo_email, 'plain'))
        server.send_message(msg)
        server.quit()
        
        return True, "✅ Historia clínica archivada correctamente."
        
    except Exception as e:
        return False, f"❌ Error al archivar: {str(e)}"

# ================= CONFIGURACIÓN DE IDIOMAS =================
IDIOMAS_DISPONIBLES = {
    "es": {"nombre": "Español", "emoji": "🇪🇸"},
    "en": {"nombre": "English", "emoji": "🇺🇸"},
    "pt": {"nombre": "Português", "emoji": "🇧🇷"},
    "fr": {"nombre": "Français", "emoji": "🇫🇷"},
    "de": {"nombre": "Deutsch", "emoji": "🇩🇪"},
    "it": {"nombre": "Italiano", "emoji": "🇮🇹"}
}

# ================= INTERFAZ SIMPLIFICADA =================
st.set_page_config(page_title="MINDGEEKCLINIC", page_icon="🧠", layout="wide")

st.title("🧠 MINDGEEKCLINIC")
st.markdown("**Sistema Profesional de Biodescodificación**")
st.markdown("---")

# Selector de idioma
idioma = st.sidebar.selectbox("🌍 Idioma", list(IDIOMAS_DISPONIBLES.keys()),
                             format_func=lambda x: f"{IDIOMAS_DISPONIBLES[x]['emoji']} {IDIOMAS_DISPONIBLES[x]['nombre']}")

# Formulario simplificado
with st.form("formulario"):
    col1, col2 = st.columns(2)
    
    with col1:
        iniciales = st.text_input("📝 Iniciales", max_chars=3)
        edad = st.number_input("🎂 Edad", min_value=1, max_value=120, value=30)
    
    with col2:
        email = st.text_input("📧 Email (opcional)", placeholder="paciente@ejemplo.com")
        tiempo = st.selectbox("⏳ Tiempo", ["Menos de 1 mes", "1-3 meses", "3-6 meses", "6-12 meses", "1-2 años", "Más de 2 años"])
    
    sintomas = st.text_area("🤒 Síntomas", height=100, placeholder="Describa sus síntomas...")
    eventos = st.text_area("⚡ Eventos emocionales", height=80, placeholder="¿Qué situaciones coinciden con los síntomas?")
    
    # Consentimiento
    st.markdown("---")
    consentimiento = st.checkbox("✅ Acepto el consentimiento informado")
    
    submitted = st.form_submit_button("🚀 Generar Diagnóstico", type="primary")
    
    if submitted:
        if not iniciales:
            st.error("❌ Iniciales requeridas")
        elif not consentimiento:
            st.error("❌ Debe aceptar el consentimiento")
        else:
            # Crear datos del paciente
            datos_paciente = {
                "id_seguro": hashlib.sha256(f"{iniciales}{edad}{datetime.now().timestamp()}".encode()).hexdigest()[:16],
                "iniciales": iniciales.upper(),
                "edad": edad,
                "email_paciente": email if email else "No proporcionado",
                "descripcion": sintomas,
                "eventos_desencadenantes": eventos,
                "tiempo_padecimiento": tiempo,
                "frecuencia": "Por evaluar",
                "estado_civil": "Por evaluar",
                "situacion_laboral": "Por evaluar",
                "tension": "Por evaluar",
                "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Simular diagnóstico
            st.session_state.paciente_actual = datos_paciente
            st.session_state.mostrar_diagnostico = True
            st.rerun()

# Mostrar diagnóstico si existe
if st.session_state.get("mostrar_diagnostico", False):
    paciente = st.session_state.paciente_actual
    
    st.markdown(f"### 📄 Paciente: {paciente['iniciales']} • {paciente['edad']} años")
    st.markdown(f"**⏳ Tiempo:** {paciente['tiempo_padecimiento']}")
    st.markdown(f"**🔒 ID:** `{paciente['id_seguro']}`")
    
    st.markdown("---")
    st.markdown("### 🔬 Diagnóstico Simulado")
    st.info("""
    **Análisis de biodescodificación:**
    
    1. **Conflicto emocional:** Basado en los eventos reportados
    2. **Significado biológico:** Los síntomas reflejan el conflicto no resuelto
    3. **Protocolo recomendado:** 3 sesiones de terapia específica
    4. **Hipnosis:** Instrucciones personalizadas disponibles
    
    *Nota: Este es un diagnóstico de ejemplo. La versión completa conecta con la biblioteca especializada.*
    """)
    
    # Enviar al correo de archivo
    st.markdown("---")
    st.markdown("### 📧 Archivo Profesional")
    
    if st.button("📨 Enviar al archivo clínico", type="primary"):
        exito, mensaje = enviar_historia_clinica_email(paciente, "Diagnóstico de biodescodificación - Ejemplo completo")
        
        if exito:
            st.success(mensaje)
            st.info("📂 Revisa: **promptandmente@gmail.com**")
        else:
            st.error(mensaje)
    
    # Botón para nuevo
    st.markdown("---")
    if st.button("🆕 Nueva Consulta"):
        st.session_state.mostrar_diagnostico = False
        st.rerun()

# Footer
st.markdown("---")
st.markdown("🧠 **MINDGEEKCLINIC v8.2** • Archivo en promptandmente@gmail.com")
