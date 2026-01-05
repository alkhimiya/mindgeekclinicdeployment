import streamlit as st
import os
from groq import Groq

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="MINDGEEKCLINIC", layout="wide", page_icon="🧠")

# Estilo Geek
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #1E3A8A; color: white; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXIÓN IA
try:
    client = Groq(api_key=st.secrets["groq"]["api_key"])
    CONEXION_IA = True
except:
    CONEXION_IA = False

# 3. SIDEBAR
with st.sidebar:
    st.title("🧠 MINDGEEKCLINIC")
    st.write("---")
    menu = st.radio("Menú", [
        "🏠 Dashboard", 
        "🤖 Admisión IA AETHON", 
        "💳 Planes y Suscripciones"
    ])
    st.write("---")
    st.caption("Avalado por Instituto AETHON")

# 4. LÓGICA DE MÓDULOS (Aquí estaba el error de sintaxis)

if menu == "🏠 Dashboard":
    st.title("Bienvenido a la Vanguardia en Salud Mental")
    st.write("Unificando Psicología, Neurociencias y Física Cuántica.")
    st.markdown("---")
    st.info("🚀 Plataforma HealthTech en construcción activa.")
    st.write("MINDGEEKCLINIC: La unión de la ciencia tradicional y las nuevas ciencias de la mente.")

elif menu == "🤖 Admisión IA AETHON":
    st.header("Analista de Admisión")
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("¿Qué situación estás atravesando?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "Eres el Analista de MINDGEEKCLINIC. Enfoque: Psiquiatría, Cuántica y Biodescodificación. Respaldo: Instituto AETHON. Plan: 4 sesiones por 80 USD vía USDT."},
                        *st.session_state.messages
                    ],
                    model="llama-3.3-70b-versatile",
                )
                response = chat_completion.choices[0].message.content
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Error: {e}")

elif menu == "💳 Planes y Suscripciones":
    st.title("Programas de Transformación")
    st.subheader("Plan Inicial de Neuroprogramación")
    st.write("**Inversión:** 80 USD (Mensual)")
    st.write("**Incluye:** 4 sesiones de Hipnosis Clínica")
    st.write("**Certifica:** Instituto Clínico de Neuroprogramación AETHON")
    st.write("---")
    st.warning("Pago vía USDT")
    
