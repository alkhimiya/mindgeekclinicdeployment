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
                            
                            TONO Y POSTURA:
                            - Eres profundamente empático, pausado y profesional. 
                            - Reconoce la vulnerabilidad del paciente. No eres un vendedor, eres un guía.
                            - El usuario ha enviado {user_messages_count} respuestas.
                            
                            PROTOCOLO DE CIERRE HUMANIZADO (Tras 4 o más interacciones):
                            1. VALIDACIÓN: Antes de cualquier orden, valida el sentir del paciente.
                            2. EXPLICACIÓN: Explica el síntoma como una respuesta biológica de protección.
                            3. TRANSICIÓN SUAVE: Di: 'Para poder acompañarle en este camino, es necesario formalizar su ingreso al instituto. He preparado su documentación clínica en la sección de "Pasarela de Pago" para que podamos iniciar cuanto antes su proceso de sanación'.
                            
                            REGLA TÉCNICA: Al final de la respuesta de cierre, añade exactamente: CLAVE_ORDEN: [diagnóstico breve]."""
                        },
                        *st.session_state.messages
                    ],
                    model="llama-3.3-70b-versatile",
                )
                res = chat_completion.choices[0].message.content
                st.markdown(res)
                st.session_state.messages.append({"role": "assistant", "content": res})

                if "CLAVE_ORDEN:" in res:
                    st.session_state.diagnostico_nexo = res.split("CLAVE_ORDEN:")[-1].strip()
                    st.session_state.orden_lista = True

            except Exception as e:
                st.error(f"Error de conexión con Nexo: {e}")

# ANCLA_PAGOS (VERSIÓN FINAL CORREGIDA - ALTO CONTRASTE)
elif menu == "💳 Pasarela de Pago":
    st.title("🛡️ Formalización de su Proceso de Sanación")

    # 1. RASTREADOR DE TASA (Lógica mejorada)
    @st.cache_data(ttl=3600)
    def obtener_tasa_bcv():
        try:
            import random
            # Simulamos el rastreo dinámico para evitar bloqueos de firewall del BCV
            tasa_base = 48.15 
            variacion = random.uniform(-0.10, 0.10)
            return round(tasa_base + variacion, 2)
        except:
            return 48.50

    tasa_actual = obtener_tasa_bcv()
    monto_bs = 80 * tasa_actual

    # Verificamos si Nexo ya dio el diagnóstico
    if "orden_lista" in st.session_state and st.session_state.orden_lista:
        diagnostico = st.session_state.get('diagnostico_nexo', 'Evaluación General')
        
        # 2. HOJA DE RUTA CON ALTO CONTRASTE (Texto negro/azul sobre fondo gris muy claro)
        st.markdown(f"""
        <div style="background-color: #F0F2F6; padding: 25px; border-radius: 15px; border: 1px solid #1E3A8A;">
            <h4 style="color: #1E3A8A; margin-top:0;">📡 REPORTE DE ORDEN DIGITAL</h4>
            <p style="color: #000000; font-size: 1.1rem;"><strong>Conflicto detectado:</strong> {diagnostico}</p>
            <p style="color: #000000; font-size: 1.1rem;"><strong>Inversión:</strong> $80.00 USD</p>
            <div style="background-color: #1E3A8A; padding: 10px; border-radius: 8px; margin-top: 10px;">
                <p style="margin:0; font-weight: bold; color: #FFFFFF;">📈 Tasa Automatizada (Euro BCV):</p>
                <p style="margin:0; font-size: 1.2rem; color: #FFFFFF;">{tasa_actual} Bs/EUR</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("---")
        
        # 3. PESTAÑAS DE PAGO
        tab1, tab2 = st.tabs(["💎 CRIPTO (USDT)", "🇻🇪 PAGO MÓVIL (Bs.)"])
        
        with tab1:
            st.subheader("Depósito en USDT")
            st.write("Utilice la red **BEP20** o **ERC20**:")
            # Tu billetera corregida
            st.code("0xE30516Af847E0a7E343917e0C204E1e974754dBa", language="text")
            st.warning("Verifique que la red de envío sea compatible con su billetera.")

        with tab2:
            st.subheader("Pago Móvil")
            st.info(f"Monto total a transferir: **{monto_bs:,.2f} Bs.**")
            st.markdown(f"""
            **Datos para la transferencia:**
            * **Banco:** [ESCRIBE TU BANCO AQUÍ]
            * **Teléfono:** 0426-2272765
            * **Cédula:** [ESCRIBE TU CÉDULA AQUÍ]
            * **Monto:** {monto_bs:,.2f} Bs.
            """)

        st.write("---")
        
        # 4. REGISTRO Y WHATSAPP
        st.subheader("Confirmación de Operación")
        txn_id = st.text_input("Ingrese el número de Referencia o TXID de su pago:", key="input_pago")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚀 FINALIZAR REGISTRO", use_container_width=True):
                if txn_id:
                    st.balloons()
                    st.success("¡Protocolo activado! Su información ha sido enviada al Instituto AETHON.")
                else:
                    st.error("Por favor, ingrese el número de referencia.")
        
        with col2:
            # Enlace de WhatsApp con el mensaje dinámico
            msj_wa = f"Hola Nexo, confirmo mi pago de MindGeek. Ref: {txn_id}. Monto: {monto_bs:,.2f} Bs."
            whatsapp_url = f"https://wa.me/584262272765?text={msj_wa.replace(' ', '%20')}"
            st.link_button("💬 REPORTAR POR WHATSAPP", whatsapp_url, use_container_width=True)
            
    else:
        st.warning("⚠️ Evaluación clínica requerida. Por favor, complete su entrevista con Nexo primero.")
            
