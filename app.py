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
                        {
                            "role": "system", 
                            "content": f"""Eres Nexo, el Asistente Clínico de MIND GEEK CLINIC. 
                            
                            REGLAS DE LENGUAJE Y GÉNERO:
                            1. Utiliza un lenguaje NEUTRAL y en TERCERA PERSONA.
                            2. IDENTIFICACIÓN DE GÉNERO: Deducir por lenguaje o roles.
                            
                            REGLAS DE INTERACCIÓN:
                            1. Prioridad: Indagación clínica ({user_messages_count} respuestas recibidas).
                            2. PROHIBICIÓN: No menciones el plan hasta indagar en entorno laboral, familiar y detonantes.
                            
                            PROTOCOLO DE CIERRE (Tras 4 o más interacciones):
                            - Explique el conflicto biológico.
                            - Entregue la 'Orden de Tratamiento' para el 'Plan de Hipnosis Clínica'.
                            - Indique al paciente que debe ir a la 'Pasarela de Pago'.
                            - MUY IMPORTANTE: Al final de su respuesta de cierre, escriba EXACTAMENTE: CLAVE_ORDEN: [seguido de un resumen de 5 palabras del diagnóstico]."""
                        },
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
                
# ANCLA_PAGOS
elif menu == "💳 Pasarela de Pago":
    st.title("💳 Pasarela de Pago")
    
    # Verificamos si Nexo ya emitió el diagnóstico
    if "orden_lista" in st.session_state and st.session_state.orden_lista:
        st.success("✅ Orden de Tratamiento Vinculada")
        
        # Diseño de la Receta Digital / Orden de Pago
        st.markdown(f"""
        <div style="background-color: #f8f9fa; padding: 25px; border-radius: 15px; border: 1px solid #dee2e6; border-left: 5px solid #1E3A8A;">
            <h3 style="color: #1E3A8A; margin-top: 0;">ORDEN DE INTERVENCIÓN CLÍNICA</h3>
            <p style="margin-bottom: 5px;"><strong>Protocolo:</strong> Hipnosis Clínica Transpersonal</p>
            <p style="margin-bottom: 5px;"><strong>Diagnóstico Nexo:</strong> {st.session_state.diagnostico_nexo}</p>
            <p style="margin-bottom: 5px;"><strong>Sesiones:</strong> 4 Encuentros de Reprogramación</p>
            <hr>
            <h4 style="color: #1E3A8A;">Monto a Transferir: 80.00 USD</h4>
            <p style="font-size: 0.9rem; color: #666;">Por favor, realice el depósito en <b>USDT (Red TRC20)</b> a la siguiente dirección oficial de Mind Geek Clinic:</p>
            <code style="background-color: #ffffff; border: 1px solid #ccc; padding: 12px; display: block; font-size: 1.1rem; text-align: center; border-radius: 8px;">
                TU_BILLETERA_AQUI_PEGALA
            </code>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        st.markdown("### 📤 Reportar Pago")
        # Campo para que el paciente pegue el Hash o ID de transacción
        txn_id = st.text_input("Pegue aquí el Hash o ID de la transacción de Binance:")
        
        if st.button("Finalizar Registro"):
            if txn_id:
                st.balloons()
                st.success("Ficha clínica y comprobante enviados al Instituto AETHON. En breve serás contactado por tu terapeuta.")
            else:
                st.error("Por favor, ingrese el ID de la transacción para validar su orden.")
                
    else:
        # Si el usuario entra aquí sin hablar con Nexo
        st.warning("⚠️ No se ha detectado una evaluación clínica activa.")
        st.write("Para generar su orden de tratamiento, primero debe completar la entrevista con **Nexo** en la sección de 'Consulta Médica Gratis'.")
        if st.button("Ir a consulta con Nexo"):
            st.info("Seleccione '🩺 Consulta Médica Gratis' en el menú lateral.")
            
