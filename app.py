import streamlit as st
import os

# Configuración de página
st.set_page_config(page_title="MindGeek Clinic", layout="wide", page_icon="🧠")

# Estilo visual (Tu Sidebar azul)
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #1E3A8A; color: white; }
    .main { background-color: #f5f7f9; }
    </style>
    """, unsafe_allow_html=True)

# --- MENÚ LATERAL ORIGINAL ---
with st.sidebar:
    st.image("https://raw.githubusercontent.com/alkhimiya/mindgeekclinicdeployment/main/static/logo.png", width=100) # Intenta cargar tu logo si existe
    st.title("MindGeek Clinic")
    st.write("---")
    menu = st.radio("Navegación", [
        "🏠 Inicio", 
        "🤖 Asistente IA (Groq/OpenAI)", 
        "👥 Gestión de Pacientes",
        "📅 Agendamiento",
        "💰 Afiliados y Pagos"
    ])

# --- LÓGICA DE LAS SECCIONES ---

if menu == "🏠 Inicio":
    st.title("Bienvenido Terapeuta")
    st.write("Selecciona una opción en el menú para comenzar.")
    
elif menu == "🤖 Asistente IA (Groq/OpenAI)":
    st.header("Asistente Terapéutico con IA")
    # Aquí es donde la app buscará tus llaves
    api_key = st.text_input("Introduce tu API Key de Groq o OpenAI (o configúrala en Secrets)", type="password")
    
    pregunta = st.chat_input("Escribe tu consulta terapéutica aquí...")
    if pregunta:
        st.info(f"Procesando consulta: {pregunta}")
        st.warning("Estamos vinculando tu función 'def chat_terapeuta' de las 5000 líneas.")

elif menu == "💰 Afiliados y Pagos":
    st.header("Panel de Stripe y Afiliados")
    st.write("Estado de conexión: **Activo**")
    # Aquí recuperaremos tu lógica de stripe

