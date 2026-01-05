import streamlit as st
import os

# 1. CONFIGURACIÓN DE PÁGINA (Debe ser lo primero)
st.set_page_config(
    page_title="MindGeek Clinic",
    layout="wide",
    page_icon="🧠"
)

# 2. ESTILO PERSONALIZADO (Sidebar Azul)
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background-color: #1E3A8A;
        color: white;
    }
    .stRadio [data-testid="stWidgetLabel"] p {
        color: white !important;
        font-weight: bold;
    }
    /* Estilo para los textos del menú */
    .st-emotion-cache-6qob1r {
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. CONEXIÓN CON SECRETS (Validación)
# Esto verifica que tus secretos estén bien escritos
try:
    GROQ_KEY = st.secrets["groq"]["api_key"]
    CONEXION_IA = True
except Exception:
    CONEXION_IA = False

# 4. MENÚ LATERAL
with st.sidebar:
    st.title("🧠 MindGeek Clinic")
    st.write("---")
    menu = st.radio("Panel de Control", [
        "🏠 Inicio", 
        "🤖 Asistente IA", 
        "👥 Pacientes",
        "📅 Agendamiento",
        "💰 Afiliados y Pagos"
    ])
    st.write("---")
    if CONEXION_IA:
        st.success("Sincronizado con Groq ✅")
    else:
        st.error("Error de conexión con IA ❌")

# 5. LÓGICA DE LAS SECCIONES
if menu == "🏠 Inicio":
    st.title("Bienvenido Terapeuta")
    st.write("### Sistema de Gestión y Asistencia IA")
    st.info("El servidor está respondiendo correctamente. Selecciona un módulo en el sidebar.")

elif menu == "🤖 Asistente IA":
    st.header("Consulta con Asistente Terapéutico")
    
    if not CONEXION_IA:
        st.warning("⚠️ Revisa tus Secrets en Streamlit. No se encuentra la api_key de Groq.")
    else:
        # Espacio para el chat
        prompt = st.chat_input("Escribe tu consulta aquí...")
        if prompt:
            with st.chat_message("user"):
                st.write(prompt)
            
            with st.chat_message("assistant"):
                st.write("Estamos listos para conectar tu función de Groq aquí.")
                st.info("Próximo paso: Pegar la lógica de respuesta de tus 5000 líneas.")

elif menu == "👥 Pacientes":
    st.header("Gestión de Pacientes")
    st.write("Aquí se mostrará la base de datos de tus pacientes.")

elif menu == "💰 Afiliados y Pagos":
    st.header("Módulo Financiero")
    # Mostramos datos de tus secretos para verificar que funcionan
    st.write(f"Tasa de comisión: **{st.secrets['affiliates']['commission_rate'] * 100}%**")
    st.write(f"Día de pago: **{st.secrets['affiliates']['payout_day']}**")

