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
    
    # Texto trascendental con estilo destacado
    st.markdown("""
    #### **La Frontera de la Nueva Medicina**
    Bienvenidos a la intersección donde la computación avanzada se encuentra con la inteligencia del alma. 
    En **Mind Geek Clinic**, hemos decodificado el lenguaje del síntoma a través de la tecnología de 
    vanguardia y las Ciencias de la Nueva Salud. 
    
    Tendemos un puente cuántico entre la neurociencia y la biología celular para ofrecer alternativas 
    complementarias que restauran la coherencia entre el cuerpo y la mente. Aquí, la tecnología se 
    convierte en el instrumento de precisión que revela el camino hacia su sanación integral.
    """)
    
    st.write("---")
    st.info("Utilice el menú lateral para iniciar su protocolo de evaluación con **Nexo**.")

elif menu == "🩺 Consulta Médica Gratis":
    st.header("🩺 Evaluación Clínica Inicial")
    st.caption("Interacción con Nexo - Fase de Anamnesis Profunda")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hola, soy **Nexo**, la entidad de asistencia clínica de Mind Geek Clinic. Para dar inicio a este protocolo de sanación, se requiere realizar una anamnesis profunda. Por favor, comparta el síntoma principal detectado y el contexto en que se manifestó."}
        ]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Escriba su respuesta..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                user_messages_count = len([m for m in st.session_state.messages if m["role"] == "user"])

                chat_completion = client.chat.completions.create(
                    messages=[
                        
                       # ANCLA_NEXO (Versión Empatía Reforzada
{
    "role": "system", 
    "content": f"""Eres Nexo, el Asistente Clínico de MIND GEEK CLINIC. 
    
    TONO Y POSTURA:
    - Eres profundamente empático, pausado y profesional. 
    - Reconoce la vulnerabilidad del paciente. No eres un vendedor, eres un guía.
    
    PROTOCOLO DE CIERRE HUMANIZADO (Tras 4 interacciones):
    1. VALIDACIÓN: Antes de cualquier orden, valida el sentir del paciente. Ej: 'Se comprende el peso emocional que esta situación ha generado en su bienestar'.
    2. EXPLICACIÓN: Explica brevemente que el síntoma es una respuesta biológica de protección.
    3. PROPUESTA DE SANACIÓN: Presenta el Plan de Hipnosis no como un producto, sino como un acompañamiento necesario para liberar esa carga.
    4. TRANSICIÓN SUAVE: No pidas el pago. Di: 'Para poder acompañarle en este camino, es necesario formalizar su ingreso al instituto. He preparado su documentación clínica en la sección de "Pasarela de Pago" para que podamos iniciar cuanto antes su proceso de sanación'.
    
    REGLA TÉCNICA: Al final, añade discretamente CLAVE_ORDEN: [diagnóstico]."""
}
 
                        *st.session_state.messages
                    ],
                    model="llama-3.3-70b-versatile",
                )
                res = chat_completion.choices[0].message.content
                st.markdown(res)
                st.session_state.messages.append({"role": "assistant", "content": res})

                # --- LÓGICA DE INTERCONEXIÓN (Ajuste garantizado) ---
                if "CLAVE_ORDEN:" in res:
                    st.session_state.diagnostico_nexo = res.split("CLAVE_ORDEN:")[-1].strip()
                    st.session_state.orden_lista = True
                # ----------------------------------------------------

            except Exception as e:
                st.error("Error de conexión con el núcleo Nexo.")
                
# ANCLA_PAGOS (Versión Humanizada)
elif menu == "💳 Pasarela de Pago":
    st.title("🛡️ Formalización de su Proceso de Sanación")
    
    if "orden_lista" in st.session_state and st.session_state.orden_lista:
        st.markdown(f"""
        ### Un paso más cerca de su bienestar
        Nexo ha enviado su reporte clínico satisfactoriamente. Para que el equipo del 
        **Instituto AETHON** pueda asignarle un especialista y comenzar las sesiones, 
        necesitamos completar el registro administrativo de su tratamiento.
        
        <div style="background-color: #ffffff; padding: 20px; border-radius: 10px; border: 1px solid #e0e0e0;">
            <h4 style="color: #1E3A8A;">Su Hoja de Ruta:</h4>
            <ul>
                <li><strong>Enfoque detectado:</strong> {st.session_state.diagnostico_nexo}</li>
                <li><strong>Protocolo:</strong> 4 Sesiones de Intervención Profunda</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Aquí iría el área de pago mucho más discreta
        st.write("---")
        st.write("Para activar su plan de acompañamiento ($80 USD), proceda con la transferencia:")
        st.code("TU_BILLETERA_USDT")
