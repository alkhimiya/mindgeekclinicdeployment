import streamlit as st
import os
from groq import Groq

# 1. CONFIGURACIÓN DE PÁGINA (Debe ser la primera instrucción de Streamlit)
st.set_page_config(page_title="MINDGEEKCLINIC", layout="wide", page_icon="🧠")

# Estilo Geek Personalizado
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #1E3A8A; color: white; }
    .stChatFloatingInputContainer { bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXIÓN CON GROQ (Cerebro de la IA)
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
        "🏠 Dashboard", 
        "🤖 Admisión IA AETHON", 
        "💳 Planes y Suscripciones"
    ])
    st.write("---")
    st.info("Respaldado por:\n**Instituto Clínico de Neuroprogramación AETHON**")

# 4. LÓGICA DE LOS MÓDULOS

# Módulo 1: Inicio
if menu == "🏠 Dashboard":
    st.title("Bienvenido a la Vanguardia en Salud Mental")
    st.write("Unificando Psicología, Neurociencias y Física Cuántica.")
    st.markdown("---")
    st.markdown("""
    ### 🚀 MINDGEEKCLINIC: HealthTech en Construcción
    Esta plataforma integra las ciencias tradicionales y las nuevas tecnologías de la mente.
    
    **Próximamente:**
    - Registro de historial clínico cuántico.
    - Seguimiento de sesiones de hipnosis.
    - Gestión de reprogramación neuronal.
    """)

# Módulo 2: Asistente IA
elif menu == "🤖 Admisión IA AETHON":
    st.header("Analista de Admisión Transdisciplinario")
    st.write("Este asistente preparará tu ficha técnica para el terapeuta.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Mostrar historial de chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Entrada de usuario
    if prompt := st.chat_input("¿Qué situación te trae hoy a MINDGEEKCLINIC?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "system", 
                            "content": """Eres el Analista de MINDGEEKCLINIC. 
                            Conocimientos: Psicología, Cuántica, Biodescodificación. 
                            Tu meta: Escuchar empáticamente y orientar hacia el Plan AETHON.
                            Plan AETHON: 4 sesiones de Hipnosis Clínica por 80 USD (pago USDT)."""
                        },
                        *st.session_state.messages
                    ],
                    model="llama-3.3-70b-versatile",
                )
                response = chat_completion.choices[0].message.content
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error("La IA está descansando un momento. Intenta de nuevo en unos segundos.")

# Módulo 3: Pagos
elif menu == "💳 Planes y Suscripciones":
    st.title("Programas de Transformación")
    st.subheader("Plan Inicial de Neuroprogramación AETHON")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Detalles del Servicio:**
        - 4 Sesiones de Hipnosis Clínica.
        - 1 Mes de acompañamiento.
        - Terapeutas Certificados por Instituto AETHON.
        
        **Inversión:** $80.00 USD
        """)
    
    with col2:
        st.warning("💳 Método de Pago: USDT")
        st.info("Para agendar, realiza el pago y contacta a soporte con el comprobante.")

