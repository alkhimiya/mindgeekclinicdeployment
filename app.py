
import streamlit as st
import os
from groq import Groq

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(page_title="MIND GEEK CLINIC", layout="wide", page_icon="🧠")

# Estilo visual para evitar deformación de texto y dar aspecto profesional
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #1E3A8A; color: white; }
    .stChatFloatingInputContainer { bottom: 20px; }
    /* Ajuste de puntaje para el título principal en móviles y desktop */
    .titulo-principal {
        font-size: 2.1rem !important;
        font-weight: 800;
        color: #1E3A8A;
        line-height: 1.1;
        margin-bottom: 5px;
    }
    .subtitulo-vanguardia {
        font-size: 1.1rem !important;
        color: #444;
        font-style: italic;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXIÓN IA
try:
    client = Groq(api_key=st.secrets["groq"]["api_key"])
    CONEXION_IA = True
except Exception as e:
    CONEXION_IA = False

# 3. SIDEBAR DE NAVEGACIÓN
with st.sidebar:
    st.title("🧠 MIND GEEK CLINIC")
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
    # Título ajustado para evitar que las palabras se amontonen o deformen
    st.markdown('<h1 class="titulo-principal">Bienvenidos a <br>Mind Geek Clinic</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitulo-vanguardia">La vanguardia en salud mental</p>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("""
    ### Tu proceso de transformación comienza aquí
    En **Mind Geek Clinic**, integramos Psicología, Neurociencias y Física Cuántica para llegar a la raíz de tu bienestar.
    
    **¿Cómo proceder?**
    1. Accede a **Consulta Médica Gratis** en el menú lateral.
    2. Inicia una conversación con **Nexo**, nuestro asistente clínico especializado.
    3. Tras la evaluación, Nexo te orientará sobre el protocolo de intervención adecuado para tu caso.
    """)

elif menu == "🩺 Consulta Médica Gratis":
    st.header("🩺 Evaluación Clínica Inicial")
    st.caption("Interacción con Nexo - Fase de Anamnesis Profunda")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Nexo está escuchando. Describe tu situación..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "system", 
                            "content": """Eres Nexo, el Asistente Clínico de MIND GEEK CLINIC. 
                            Eres un profesional experto en Medicina Germánica, Biodescodificación y Neurociencias.
                            
                            TU OBJETIVO CLÍNICO:
                            1. Presentarte como Nexo y realizar una anamnesis profunda.
                            2. Debes indagar en: tiempo del padecimiento, eventos desencadenantes en el entorno, situación emocional, familiar y laboral actual.
                            3. No te comportes como un vendedor. Tu prioridad es el diagnóstico profesional del conflicto biológico.
                            4. Solo tras una indagación exhaustiva, recomienda el: 'Plan de hipnosis clínica para el tratamiento de su condición'.
                            
                            DETALLES DEL TRATAMIENTO:
                            - Consiste en 4 sesiones de intervención profunda.
                            - Inversión: 80 USD (Pago Único).
                            - Método de pago: USDT.
                            
                            Habla de forma pausada, empática y con alto rigor profesional."""
                        },
                        *st.session_state.messages
                    ],
                    model="llama-3.3-70b-versatile",
                )
                res = chat_completion.choices[0].message.content
                st.markdown(res)
                st.session_state.messages.append({"role": "assistant", "content": res})
            except:
                st.error("Nexo ha perdido la conexión momentáneamente. Por favor, reintenta.")

elif menu == "💳 Planes y Suscripciones":
    st.title("Tratamientos Especializados")
    st.subheader("Plan de Hipnosis Clínica para el tratamiento de su condición")
    
    st.markdown("""
    Protocolo de intervención diseñado tras la evaluación clínica inicial.
    
    - **Servicio:** 4 Sesiones de Hipnosis Clínica Transpersonal.
    - **Metodología:** Reprogramación neuronal y Biodescodificación.
    - **Inversión:** $80.00 USD (**Pago Único**).
    - **Certificación:** Instituto Clínico de Neuroprogramación AETHON.
    ---
    **Instrucciones de Pago:**
    El pago se realiza exclusivamente vía **USDT (Red TRC20)**. Una vez completado, envía el comprobante para asignar tu fecha de inicio.
    """)
