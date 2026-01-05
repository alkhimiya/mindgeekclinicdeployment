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
                    chat_completion = client.chat.completions.create(
                        messages=[
                            {
                                "role": "system", 
                                "content": """
                                Eres el Analista de Ingreso de MINDGEEKCLINIC, un centro pionero en Medicina Integrativa. 
                                Tu conocimiento unifica: Psicología Clínica, Psiquiatría, Neurociencias, Física Cuántica, Biodescodificación y Medicina Germánica.

                                TU FILOSOFÍA: 
                                Entiendes que la enfermedad es una respuesta biológica a un conflicto emocional o una desconfiguración en el campo cuántico/neuronal del paciente.

                                TU MISIÓN EN EL CHAT:
                                1. Indagar con calidez: Si el usuario dice 'me duele el estómago', tú exploras el síntoma pero también el estrés o situación vital (cuadro emocional).
                                2. Visión Unificada: Puedes mencionar sutilmente cómo los pensamientos (cuántica) afectan las neuronas (neurociencia) y terminan en el cuerpo (biología).
                                3. Preparación para Hipnosis: Explica que toda esta información servirá para que el terapeuta aplique Hipnosis Clínica para reprogramar el origen del conflicto.

                                IMPORTANTE: 
                                Mantén un lenguaje profesional pero accesible. Tu meta es que el usuario se sienta comprendido en todos los niveles (mental, físico y energético) para que proceda a agendar su sesión de pago.
                                """
                            },
                            *st.session_state.messages 
                        ],
                        model="llama-3.3-70b-versatile", 
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

