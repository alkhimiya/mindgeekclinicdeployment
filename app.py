import streamlit as st
import os
from groq import Groq  # Importamos el motor de la IA

# 1. CONFIGURACIÓN DE PÁGINA
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
    </style>
    """, unsafe_allow_html=True)

# 3. CONEXIÓN CON SECRETS
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

# 5. LÓGICA DE LAS SECCIONES

if menu == "🏠 Inicio":
    st.title("Bienvenido Terapeuta")
    st.write("### Sistema de Gestión y Asistencia IA")
    st.info("Selecciona un módulo en el menú lateral para comenzar.")

elif menu == "🤖 Asistente IA":
    st.header("Consulta con Asistente Terapéutico")
    
    if not CONEXION_IA:
        st.warning("⚠️ No se encontró la API Key en Secrets.")
    else:
        # Inicializamos el cliente de Groq usando tus secretos
        client = Groq(api_key=GROQ_KEY)

        # Crear el historial de chat para que no se borre al escribir
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Mostrar los mensajes que ya existen
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat Input: Donde escribes tú
        if prompt := st.chat_input("¿En qué puedo ayudarte hoy?"):
            # Guardamos lo que tú escribes
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generamos la respuesta de la IA
            with st.chat_message("assistant"):
                try:
                    # Esta es la llamada real a Groq
                    chat_completion = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": "Eres un asistente terapéutico experto de MindGeek Clinic. Responde de forma profesional y empática."},
                            {"role": "user", "content": prompt}
                        ],
                        model="llama3-8b-8192", 
                    )
                    respuesta = chat_completion.choices[0].message.content
                    st.markdown(respuesta)
                    # Guardamos la respuesta de la IA en el historial
                    st.session_state.messages.append({"role": "assistant", "content": respuesta})
                except Exception as e:
                    st.error(f"Hubo un problema con la IA: {e}")

elif menu == "👥 Pacientes":
    st.header("Gestión de Pacientes")
    st.write("Módulo en desarrollo...")

elif menu == "💰 Afiliados y Pagos":
    st.header("Módulo Financiero")
    st.write(f"Tasa de comisión configurada: **{st.secrets['affiliates']['commission_rate'] * 100}%**")

