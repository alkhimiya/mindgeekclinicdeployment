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
    "🏢 Área Administrativa" # <-- Cambiado de "Pasarela de Pago"
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

# ANCLA_PAGOS (Versión Triangulación USD -> EUR -> BS)
elif menu == "💳 Pasarela de Pago":
    st.title("🛡️ Formalización de su Proceso de Sanación")

    # 1. CEREBRO FINANCIERO (Triangulación USD -> EUR -> BS)
    @st.cache_data(ttl=3600)
    def calcular_montos_reales():
        tasa_euro_bcv = 360.50  # Tasa según tu reporte del BCV
        paridad_eur_usd = 0.92  # 1 USD = 0.92 EUR (Paridad internacional)
        monto_usd = 80.00
        monto_eur = monto_usd * paridad_eur_usd
        monto_bs = monto_eur * tasa_euro_bcv
        return tasa_euro_bcv, monto_eur, monto_bs

    # Activamos los cálculos
    tasa_bcv, total_eur, total_bs = calcular_montos_reales()

    if "orden_lista" in st.session_state and st.session_state.orden_lista:
        diag = st.session_state.get('diagnostico_nexo', 'Evaluación General')
        
        # 2. CUADRO DE ORDEN DIGITAL (Alto Contraste)
        st.markdown(f"""
        <div style="background-color: #F0F2F6; padding: 25px; border-radius: 15px; border: 1px solid #1E3A8A;">
            <h4 style="color: #1E3A8A; margin-top:0;">📡 REPORTE DE ORDEN SINCRONIZADO</h4>
            <p style="color: #000; margin-bottom:5px;"><strong>Enfoque Clínico:</strong> {diag}</p>
            <p style="color: #000; margin-bottom:5px;"><strong>Inversión Base:</strong> $80.00 USD ({total_eur:.2f} €)</p>
            <hr style="border: 0.5px solid #1E3A8A;">
            <div style="background-color: #1E3A8A; padding: 15px; border-radius: 8px;">
                <p style="margin:0; font-weight: bold; color: #FFFFFF; font-size: 0.9rem;">📈 TASA OFICIAL EUR (BCV):</p>
                <p style="margin:0; font-size: 1.3rem; color: #FFFFFF;">{tasa_bcv:.2f} Bs/EUR</p>
                <p style="margin:5px 0 0 0; font-weight: bold; color: #FFD700; font-size: 1.4rem;">TOTAL A PAGAR: {total_bs:,.2f} Bs.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("---")
        
        # 3. PESTAÑAS DE PAGO
        tab1, tab2 = st.tabs(["🇻🇪 PAGO MÓVIL (Mercantil)", "💎 CRIPTO (USDT)"])
        
        with tab1:
            st.markdown(f"""
            <div style="background-color: #FFFFFF; padding: 20px; border-radius: 10px; border: 1px solid #dee2e6;">
                <h4 style="color: #1E3A8A;">Datos para Pago Móvil:</h4>
                <p style="color: #000;"><strong>Banco:</strong> Banco Mercantil</p>
                <p style="color: #000;"><strong>Cédula:</strong> V-15.214.337</p>
                <p style="color: #000;"><strong>Teléfono:</strong> 04262272765</p>
                <h3 style="color: #1E3A8A; border-top: 1px solid #eee; padding-top:10px;">Monto: {total_bs:,.2f} Bs.</h3>
            </div>
            """, unsafe_allow_html=True)

        with tab2:
            st.subheader("Depósito en Cripto")
            st.write("Redes: **BEP20 / ERC20**")
            st.code("0xE30516Af847E0a7E343917e0C204E1e974754dBa", language="text")

        st.write("---")
        
        # 4. CONFIRMACIÓN Y WHATSAPP
        txn_id = st.text_input("Ingrese el número de Referencia bancaria:", key="pago_final")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 CONFIRMAR REGISTRO", use_container_width=True):
                if txn_id:
                    st.balloons()
                    st.success("¡Referencia recibida! El equipo validará su ingreso.")
                else:
                    st.error("Por favor, ingrese la referencia.")
        
        with col2:
            msj_wa = f"Hola Nexo, confirmo mi pago de MindGeek. Ref: {txn_id}. Monto: {total_bs:,.2f} Bs."
            url_wa = f"https://wa.me/584262272765?text={msj_wa.replace(' ', '%20')}"
            st.link_button("💬 NOTIFICAR POR WHATSAPP", url_wa, use_container_width=True)
            
    else:
        st.warning("⚠️ Se requiere una evaluación clínica previa con Nexo para generar la orden de pago.")
