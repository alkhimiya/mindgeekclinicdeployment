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
    st.caption("Interacción con Nexo - Fase de Anamnesis Profunda")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hola, soy **Nexo**, su asistente clínico. Para iniciar este proceso de sanación, es imperativo realizar una anamnesis profunda de su situación. Por favor, descríbame su síntoma principal y bajo qué contexto emocional o familiar se manifestó por primera vez."}
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
                # Calculamos cuántas veces ha hablado el usuario para controlar el cierre
                user_messages_count = len([m for m in st.session_state.messages if m["role"] == "user"])

                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "system", 
                            "content": f"""Eres Nexo, el Asistente Clínico de MIND GEEK CLINIC. Profesional experto en Medicina Germánica y Biodescodificación.
                            
                            REGLAS DE INTERACCIÓN:
                            1. Tu prioridad absoluta es la indagación. No puedes saltar al cierre sin antes preguntar por: cronicidad, entorno laboral, dinámica familiar y eventos detonantes específicos.
                            2. El usuario ha enviado {user_messages_count} mensajes. 
                            3. PROHIBICIÓN: NO menciones el 'Plan de Hipnosis' ni la 'Pasarela de Pago' hasta que tengas una visión clara del conflicto (mínimo 3 o 4 interacciones de calidad).
                            4. CUANDO LLEGUE EL MOMENTO DEL CIERRE (y solo una vez): 
                               - Explica el conflicto biológico detectado.
                               - Di: 'Basado en el perfil clínico que hemos trazado, he generado su Orden de Tratamiento. Usted requiere la aplicación del "Plan de Hipnosis Clínica para el tratamiento de su condición", que consta de 4 sesiones de intervención profunda.'
                               - Deriva al paciente a la 'Pasarela de Pago' en el menú lateral para formalizar su ingreso.
                            5. Si el paciente aún está describiendo síntomas, continúa profundizando con preguntas clínicas.
                            
                            Inversión: 80 USD (Pago Único). Tono: Empático, analítico y serio."""
                        },
                        *st.session_state.messages
                    ],
                    model="llama-3.3-70b-versatile",
                )
                res = chat_completion.choices[0].message.content
                st.markdown(res)
                st.session_state.messages.append({"role": "assistant", "content": res})
            except:
                st.error("Error de conexión.")

elif menu == "💳 Pasarela de Pago":
    st.title("💳 Pasarela de Pago")
    st.info("Espacio para la formalización de la Orden de Tratamiento generada por Nexo.")

