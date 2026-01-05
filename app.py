import streamlit as st
import os
from groq import Groq

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="MINDGEEKCLINIC", layout="wide", page_icon="🧠")

# Estilo Geek Personalizado
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #1E3A8A; color: white; }
    .stChatFloatingInputContainer { bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXIÓN CON GROQ
try:
    client = Groq(api_key=st.secrets["groq"]["api_key"])
    CONEXION_IA = True
except Exception as e:
    CONEXION_IA = False
    st.error(f"Error de conexión con la IA: {e}")

# 3. SIDEBAR DE NAVEGACIÓN
with st.sidebar:
    st.title("🧠 MINDGEEKCLINIC")
    st.caption("Vanguardia en Salud Mental")
    st.write("---")
    menu = st.radio("Menú Principal", [
        "🏠 Inicio", 
        "🩺 Consulta Médica Gratis", 
        "💳 Planes y Suscripciones"
    ])
    st.write("---")
    st.info("Respaldado por:\n**Instituto Clínico de Neuroprogramación AETHON**")

# 4. LÓGICA DE LOS MÓDULOS

# Módulo 1: Inicio
if menu == "🏠 Inicio":
    st.title("Bienvenido a la Vanguardia en Salud Mental")
    st.write("Unificando Psicología, Neurociencias y Física Cuántica.")
    st.markdown("---")
    st.markdown("""
    ### 🚀 MINDGEEKCLINIC: HealthTech en Construcción
    Bienvenido a un espacio donde la ciencia tradicional y las nuevas tecnologías de la mente se encuentran para tu bienestar.
    
    **¿Cómo empezar?**
    1. Dirígete a la sección de **Consulta Médica Gratis**.
    2. Cuéntanos qué te sucede. Nuestra IA evaluará tu caso bajo los principios de AETHON.
    3. Obtén una recomendación para iniciar tu proceso de reprogramación neuronal.
    """)

# Módulo 2: Consulta Médica Gratis (IA)
elif menu == "🩺 Consulta Médica Gratis":
    st.header("🩺 Tu Primera Consulta de Orientación")
    st.write("Cuéntame qué te sucede. Estoy aquí para escucharte y preparar tu ficha para el equipo de terapeutas.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Mostrar historial de chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Entrada de usuario
    if prompt := st.chat_input("¿En qué puedo ayudarte hoy?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "system", 
                            "content": """Eres el Consultor Inicial de MINDGEEKCLINIC. Tu tono es cálido, médico y profesional.
                            Manejas conocimientos de: Psicología, Psiquiatría, Cuántica, Biodescodificación y Medicina Germánica. 
                            
                            TU MISIÓN:
                            1. Escuchar el síntoma y preguntar por el conflicto emocional detrás (Biodescodificación).
                            2. Explicar que esta es una consulta de orientación inicial gratuita.
                            3. Sugerir el 'Plan de Neuroprogramación AETHON' de 4 sesiones por 80 USD para tratar la raíz con hipnosis clínica.
                            4. Informar que los pagos son vía USDT."""
                        },
                        *st.session_state.messages
                    ],
                    model="llama-3.3-70b-versatile",
                )
                response = chat_completion.choices[0].message.content
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error("Estamos recibiendo muchas consultas. Por favor, espera un momento.")

# Módulo 3: Pagos
elif menu == "💳 Planes y Suscripciones":
    st.title("Programas de Transformación")
    st.subheader("Plan Inicial de Neuroprogramación AETHON")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Detalles del Servicio:**
        - 4 Sesiones de Hipnosis Clínica.
        - 1 Mes de acompañamiento continuo.
        - Terapeutas Certificados por el **Instituto AETHON**.
        
        **Inversión:** $80.00 USD
        """)
    
    with col2:
        st.warning("💳 Método de Pago: USDT (Billetera Electrónica)")
        st.info("Una vez realizado el pago, contacta a soporte para asignar tu terapeuta certificado.")

