import streamlit as st

# 1. Configuración básica
st.set_page_config(page_title="MindGeek Clinic - Rescate", layout="wide", page_icon="🧠")

# 2. Estilo para recuperar tu Sidebar azul
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #1E3A8A; color: white; }
    </style>
    """, unsafe_allow_html=True)

# 3. Menú Lateral
with st.sidebar:
    st.title("🧠 MindGeek Clinic")
    st.write("---")
    opcion = st.radio("Panel de Control:", [
        "🏠 Inicio", 
        "🤖 Diagnóstico IA", 
        "👥 Pacientes",
        "💰 Pagos y Afiliados"
    ])

# 4. Contenido Principal
if opcion == "🏠 Inicio":
    st.title("Sistema Recuperado")
    st.success("¡Bienvenido! Hemos logrado que el servidor vuelva a la vida.")
    st.info("Ahora ya no tienes el error 503. El siguiente paso es traer tu lógica de IA aquí.")

elif opcion == "🤖 Diagnóstico IA":
    st.header("Módulo de IA")
    st.write("Reconectando con Groq y Anthropic...")

