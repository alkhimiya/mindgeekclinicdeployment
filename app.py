import streamlit as st
import os
from groq import Groq

# 1. CONFIGURACIÓN DE VANGUARDIA
st.set_page_config(page_title="MINDGEEKCLINIC | HealthTech", layout="wide", page_icon="🧠")

# Estilo Profesional
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #1E3A8A; color: white; }
    .stAlert { border-radius: 10px; border: 1px solid #1E3A8A; }
    h1, h2 { color: #1E3A8A; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXIÓN IA
try:
    client = Groq(api_key=st.secrets["groq"]["api_key"])
    CONEXION_IA = True
except:
    CONEXION_IA = False

# 3. SIDEBAR DE NAVEGACIÓN
with st.sidebar:
    st.title("🧠 MINDGEEKCLINIC")
    st.caption("Salud Mental de Vanguardia")
    st.write("---")
    menu = st.radio("Módulos HealthTech", [
        "🏠 Dashboard", 
        "🤖 Admisión IA AETHON", 
        "💳 Planes y Suscripciones",
        "📂 Mi Historial"
    ])
    st.write("---")
    st.info("Avalado por: \n**Instituto Clínico de Neuroprogramación AETHON**")

# 4. LÓGICA DE MÓDULOS

elif menu == "🏠 Dashboard":
    st.title("MINDGEEKCLINIC")
    st.subheader("Vanguardia en Salud Mental e Hipnosis Clínica")
    
    st.markdown("""
    ---
    ### 🧠 Visión Integrativa
    Unificando Psicología, Neurociencias y Física Cuántica para la reprogramación neuronal.
    
    **Estado de la plataforma:** 🚀 HealthTech en construcción activa.
    ---
    """)
    
    st.info("💡 Consejo: Una vez que subas tu logo al repositorio, aparecerá automáticamente aquí.")
    
elif menu == "🤖 Admisión IA AETHON":
    st.header("Analista de Admisión Transdisciplinario")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Cuéntame, ¿qué situación estás atravesando?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # SYSTEM PROMPT OPTIMIZADO PARA HEALTHTECH
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": """
                    Eres el Analista Senior de MINDGEEKCLINIC. 
                    Tu enfoque unifica Psiquiatría, Cuántica, Biodescodificación y Neurociencias.
                    TU MISIÓN: Escuchar el síntoma, identificar el conflicto biológico/emocional y proponer el PLAN AETHON.
                    
                    SOBRE EL PLAN: 
                    - 4 sesiones de Hipnosis Clínica (1 mes).
                    - Inversión: 80 USD.
                    - Certificación: Instituto Clínico de Neuroprogramación AETHON.
                    - Objetivo: Reprogramación neuronal profunda.
                    
                    Si el usuario parece listo, invítalo a la sección de 'Planes y Suscripciones'.
                    """},
                    *st.session_state.messages
                ],
                model="llama-3.3-70b-versatile",
            )
            response = chat_completion.choices[0].message.content
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

elif menu == "💳 Planes y Suscripciones":
    st.title("Programas de Transformación")
    st.subheader("Plan Inicial de Neuroprogramación")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write("""
        ### Beneficios del Programa:
        * **4 Sesiones Personalizadas** con terapeutas certificados por AETHON.
        * **Enfoque Integrativo:** Trabajo sobre la causa raíz (Biodecodificación).
        * **Herramientas:** Hipnosis Clínica y Reprogramación Neuronal.
        * **Duración:** 30 días de acompañamiento.
        """)
        st.markdown("### Inversión: **80.00 USD**")

    with col2:
        st.success("✅ Certificación AETHON")
        st.warning("💳 Pago vía USDT")
        st.code("DIRECCION_DE_BILLETERA_AQUI", language="text")
        st.caption("Envía el hash de la transacción al soporte una vez realizado.")

