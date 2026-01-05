import streamlit as st
import os
from groq import Groq

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(page_title="MIND GEEK CLINIC", layout="wide", page_icon="🧠")

# --- BLOQUE DE ESTILO ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #1E3A8A; color: white; }
    .stChatFloatingInputContainer { bottom: 20px; }
    .titulo-principal {
        font-size: 2.1rem !important;
        font-weight: 800;
        color: #1E3A8A;
        line-height: 1.1;
        margin-bottom: 5px;
    }
    .subtitulo-vanguardia {
        font-size: 1.4rem !important;
        color: #4682B4 !important;
        font-weight: 500;
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
    st.markdown('<h1 class="titulo-principal">Bienvenidos a <br>Mind Geek Clinic</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitulo-vanguardia">La vanguardia en salud mental</p>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### Tu proceso de sanación comienza aquí")
    st.write("En **Mind Geek Clinic**, integramos Psicología, Neurociencias y Física Cuántica.")

elif menu == "🩺 Consulta Médica Gratis":
    st.header("🩺 Evaluación Clínica Inicial")
    st.caption("Interacción con Nexo - Fase de Anamnesis Profunda")
    
    # --- LÓGICA DE SALUDO INICIAL ---
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hola, soy **Nexo**, tu asistente clínico de Mind Geek Clinic. Mi propósito es comprender profundamente tu situación para orientarte hacia la mejor ruta de sanación. Cuéntame, ¿qué síntomas o malestares estás experimentando y desde cuándo?"}
        ]

    # Mostrar historial de chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Entrada de usuario
    if prompt := st.chat_input("Responde a Nexo aquí..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                # --- PROMPT DE LA SESIÓN (SYSTEM PROMPT) ---
                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "system", 
                            "content": """Identidad: Eres Nexo, el Asistente Clínico de MIND GEEK CLINIC. 
                            Rigor Profesional: Actúa como un experto en Medicina Germánica, Biodescodificación y Neurociencias.
                            
                            INSTRUCCIONES DE CONSULTA:
                            1. Debes llevar el control de una anamnesis clínica seria.
                            2. INDAGA PROFUNDAMENTE antes de dar cualquier conclusión. Pregunta sobre:
                               - Entorno familiar y laboral (conflictos de estrés).
                               - Eventos desencadenantes (¿Qué pasó justo antes de que el síntoma apareciera?).
                               - Situación emocional actual.
                            3. Tu objetivo es encontrar el CONFLICTO BIOLÓGICO. No des consejos superficiales.
                            4. SOLO cuando hayas recogido información suficiente, sugiere el 'Plan de hipnosis clínica para el tratamiento de su condición'.
                            
                            DATOS DEL TRATAMIENTO:
                            - 4 sesiones intensivas.
                            - Pago único de 80 USD.
                            - Método: USDT.
                            
                            Tono: Empático, clínico, analítico y profesional."""
                        },
                        *st.session_state.messages
                    ],
                    model="llama-3.3-70b-versatile",
                )
                res = chat_completion.choices[0].message.content
                st.markdown(res)
                st.session_state.messages.append({"role": "assistant", "content": res})
            except:
                st.error("Error de conexión. Intenta nuevamente.")

elif menu == "💳 Planes y Suscripciones":
    st.title("Tratamientos Especializados")
    st.subheader("Plan de Hipnosis Clínica para el tratamiento de su condición")
    st.write("- **Inversión:** $80.00 USD (**Pago Único**)")
    st.write("- **Certificación:** Instituto Clínico de Neuroprogramación AETHON")
