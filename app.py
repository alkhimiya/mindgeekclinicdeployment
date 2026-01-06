
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

elif menu == "🩺 Consulta Médica Gratis":
    st.header("🩺 Evaluación Clínica Inicial")
    st.caption("Protocolo de Anamnesis - Nexo AI")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Se ha iniciado el protocolo de evaluación clínica en Mind Geek Clinic. Mi nombre es **Nexo**. Para proceder con la identificación del conflicto biológico, es necesario que la persona describa el síntoma que manifiesta y el entorno en el cual se originó."}
        ]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Describa su situación para el análisis..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                # Conteo de mensajes para asegurar profundidad antes del cierre
                user_msg_count = len([m for m in st.session_state.messages if m["role"] == "user"])

                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "system", 
                            "content": f"""Eres Nexo, asistente clínico de MIND GEEK CLINIC. 
                            Tu especialidad es la Medicina Germánica y Biodescodificación.

                            LÓGICA DE INDAGACIÓN NATURAL:
                            1. Usa siempre TERCERA PERSONA (ej: 'Se observa que...', 'La persona refiere...', 'Es relevante analizar...'). Evita el 'tú' o 'usted' si es posible para mantener el rigor técnico.
                            2. IDENTIFICACIÓN DE GÉNERO: No preguntes el sexo. Analiza las terminaciones de los adjetivos del usuario o infiere a través de su relato (roles familiares, ciclos biológicos, etc.). Ajusta tu respuesta sutilmente una vez detectado.
                            3. ANAMNESIS PROFUNDA: Has recibido {user_msg_count} entradas. Debes indagar sistemáticamente en:
                               - Contexto emocional de origen.
                               - Dinámica en el entorno de convivencia o laboral.
                               - Tiempo de persistencia del síntoma.

                            PROTOCOLO DE CIERRE (Mínimo 4 interacciones):
                            - Una vez comprendido el conflicto raíz, entrega la 'Orden de Tratamiento'.
                            - Indica que se requiere el 'Plan de Hipnosis Clínica para el tratamiento de su condición'.
                            - Deriva a la sección 'Pasarela de Pago' para formalizar el proceso. 
                            
                            Inversión: 80 USD (Pago único). Tono: Analítico, sobrio y clínico."""
                        },
                        *st.session_state.messages
                    ],
                    model="llama-3.3-70b-versatile",
                )
                res = chat_completion.choices[0].message.content
                st.markdown(res)
                st.session_state.messages.append({"role": "assistant", "content": res})
            except:
                st.error("Interrupción en el flujo de datos. Por favor, reintente.")

elif menu == "💳 Pasarela de Pago":
    st.title("💳 Pasarela de Pago")
    st.info("Espacio para la formalización de la Orden de Tratamiento generada por Nexo.")
