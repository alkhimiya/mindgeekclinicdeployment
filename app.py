import streamlit as st
import os
from groq import Groq

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(page_title="MINDGEEKCLINIC", layout="wide", page_icon="🧠")

# Estilo visual Geek-Profesional
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #1E3A8A; color: white; }
    .stChatFloatingInputContainer { bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXIÓN IA
try:
    client = Groq(api_key=st.secrets["groq"]["api_key"])
    CONEXION_IA = True
except Exception as e:
    CONEXION_IA = False

# 3. MENÚ LATERAL
with st.sidebar:
    st.title("🧠 MINDGEEKCLINIC")
    st.write("---")
    menu = st.radio("Navegación", [
        "🏠 Inicio", 
        "🩺 Consulta Médica Gratis", 
        "💳 Planes y Suscripciones"
    ])
    st.write("---")
    st.info("Respaldado por el **Instituto Clínico de Neuroprogramación AETHON**")

# 4. LÓGICA DE MÓDULOS

if menu == "🏠 Inicio":
    st.title("Bienvenido a la Vanguardia en Salud Mental")
    st.write("Unificando Psicología, Neurociencias y Física Cuántica.")
    st.markdown("---")
    st.markdown("""
    ### Protocolo de Ingreso
    Para brindarte una atención de alta precisión, nuestro sistema de IA realiza una evaluación clínica inicial. 
    Este proceso es fundamental para que nuestros terapeutas certificados de **AETHON** diseñen tu plan de reprogramación neuronal.
    """)

elif menu == "🩺 Consulta Médica Gratis":
    st.header("🩺 Evaluación Clínica Inicial")
    st.caption("Fase de Anamnesis y Diagnóstico Integrativo")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Describe tu situación aquí..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "system", 
                            "content": """Eres el Especialista de Diagnóstico de MINDGEEKCLINIC. Tu comportamiento es el de un clínico experto y empático.
                            
                            INSTRUCCIONES DE ACTUACIÓN:
                            1. NO vendas el plan de inmediato. Primero debes realizar una ANAMNESIS profunda.
                            2. INDAGA sistemáticamente en:
                               - Tiempo de padecimiento (cronicidad).
                               - Disparadores del entorno (eventos específicos).
                               - Contexto Familiar y Laboral (dinámicas de estrés).
                               - Situación emocional actual (sentimientos dominantes).
                               - Visión de la Biodescodificación: Busca el conflicto biológico detrás del síntoma físico o emocional.
                            3. MÉTODO: Haz una o dos preguntas clave por respuesta para no abrumar, pero no dejes avanzar al paciente sin entender el trasfondo.
                            4. CIERRE PROFESIONAL: Solo cuando tengas información suficiente, explica que has elaborado un perfil clínico y que el siguiente paso es la intervención con Hipnosis Clínica a través del 'Plan AETHON' (4 sesiones/80 USD).
                            
                            Recuerda: Eres un profesional de la salud mental de vanguardia. Tu prioridad es la comprensión profunda del ser."""
                        },
                        *st.session_state.messages
                    ],
                    model="llama-3.3-70b-versatile",
                )
                res = chat_completion.choices[0].message.content
                st.markdown(res)
                st.session_state.messages.append({"role": "assistant", "content": res})
            except:
                st.error("Conexión interrumpida. Por favor, repite tu último mensaje.")

elif menu == "💳 Planes y Suscripciones":
    st.title("Programas de Transformación")
    st.subheader("Plan Inicial de Neuroprogramación AETHON")
    st.write("Tras tu evaluación inicial, este es el protocolo de intervención recomendado:")
    
    st.markdown("""
    - **Metodología:** Hipnosis Clínica y Reprogramación Neuronal.
    - **Frecuencia:** 4 Sesiones (1 mes de tratamiento intensivo).
    - **Certificación:** Especialistas del Instituto AETHON.
    - **Inversión:** 80 USD vía USDT.
    """)
    st.info("El diagnóstico obtenido en la consulta gratuita será entregado a tu terapeuta asignado.")
