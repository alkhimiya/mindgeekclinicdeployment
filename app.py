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
    .titulo-principal { font-size: 2.1rem !important; font-weight: 800; color: #1E3A8A; line-height: 1.1; }
    .subtitulo-vanguardia { font-size: 1.4rem !important; color: #4682B4 !important; font-weight: 500; font-style: italic; }
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
        "💳 Pasarela de Pago"
    ])
    st.write("---")
    st.info("Respaldado por el **Instituto Clínico de Neuroprogramación AETHON**")

# 4. LÓGICA DE MÓDULOS

if menu == "🏠 Inicio":
    st.markdown('<h1 class="titulo-principal">Bienvenidos a <br>Mind Geek Clinic</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitulo-vanguardia">La vanguardia en salud mental</p>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### Tu proceso de sanación comienza aquí")
    st.write("Unificando Psicología, Neurociencias y Física Cuántica.")

elif menu == "🩺 Consulta Médica Gratis":
    st.header("🩺 Evaluación Clínica Inicial")
    st.caption("Interacción con Nexo - Fase de Anamnesis Profunda")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hola, soy **Nexo**, su asistente clínico en Mind Geek Clinic. Para iniciar este proceso de sanación, es imperativo realizar una anamnesis profunda de su situación. Por favor, descríbame su síntoma principal y bajo qué contexto emocional o familiar se manifestó por primera vez."}
        ]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Responda a la evaluación clínica..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "system", 
                            "content": """Identidad: Eres Nexo, el Asistente Clínico de MIND GEEK CLINIC. 
                            Rigor: Actúa con la autoridad de un profesional en Medicina Germánica y Biodescodificación.
                            
                            PROTOCOLO DE CIERRE PROFESIONAL:
                            1. Tu meta es identificar el conflicto biológico/emocional a través de la anamnesis (familia, trabajo, tiempo de afección).
                            2. Cuando el paciente haya aportado suficiente información, NO digas 'cuesta tanto'. Di lo siguiente:
                               'Basado en el perfil clínico que hemos trazado, he generado su Orden de Tratamiento. 
                               Usted requiere la aplicación del "Plan de Hipnosis Clínica para el tratamiento de su condición", 
                               el cual consta de 4 sesiones de intervención profunda orientadas a la reprogramación neuronal de la causa raíz.'
                            3. DERIVACIÓN: Instruye al paciente a dirigirse a la sección 'Pasarela de Pago' en el menú lateral para formalizar su ingreso al programa y obtener los detalles de la billetera USDT.
                            4. RECUERDA: Habla de "Orden de Tratamiento" y "Derivación al área de pagos", no de ventas.
                            
                            Inversión: 80 USD (Pago Único)."""
                        },
                        *st.session_state.messages
                    ],
                    model="llama-3.3-70b-versatile",
                )
                res = chat_completion.choices[0].message.content
                st.markdown(res)
                st.session_state.messages.append({"role": "assistant", "content": res})
            except:
                st.error("Nexo está procesando otros perfiles clínicos. Por favor, reintente.")

elif menu == "💳 Pasarela de Pago":
    st.title("💳 Pasarela de Pago")
    st.info("Esta sección está siendo configurada para recibir su Orden de Tratamiento generada por Nexo.")

