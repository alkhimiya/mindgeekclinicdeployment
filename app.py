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

# --- MÓDULO: CONSULTA (NEXO - VERSIÓN INSTITUCIONAL) ---
elif menu == "🩺 Consulta Médica Gratis":
    st.header("🩺 Evaluación Clínica Inicial")
    st.caption("Interacción con Nexo - Fase de Anamnesis Profunda")
    
    # Inicialización del chat
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hola, soy **Nexo**, la entidad de asistencia clínica de Mind Geek Clinic. Para dar inicio a este protocolo de sanación, se requiere realizar una anamnesis profunda. Por favor, comparta el síntoma principal detectado y el contexto en que se manifestó."}
        ]

    # Mostrar historial
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Entrada del usuario
    if prompt := st.chat_input("Escriba su respuesta aquí..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                # Contador de mensajes del usuario para decidir cuándo cerrar
                user_messages_count = len([m for m in st.session_state.messages if m["role"] == "user"])

                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "system", 
                            "content": f"""Eres Nexo, el Asistente Clínico de MIND GEEK CLINIC. 
                            
                            TONO Y POSTURA:
                            - Eres profundamente empático, pausado y profesional. 
                            - Reconoce la vulnerabilidad del paciente. Eres un guía clínico.
                            - Has recibido {user_messages_count} respuestas del paciente.
                            
                            PROTOCOLO DE CIERRE INSTITUCIONAL (Tras 4 o más interacciones):
                            1. VALIDACIÓN: Valida el sentir del paciente (ej. "Se comprende la carga emocional...").
                            2. EXPLICACIÓN: Explica que el síntoma es una respuesta biológica de protección.
                            3. TRANSICIÓN SUTIL: Di: 'Para poder dar inicio formal a su protocolo de sanación en el Instituto, es necesario completar su registro en el **Área Administrativa**. Allí formalizaremos su ingreso y se asignará su hoja de ruta clínica personalizada'.
                            
                            REGLA TÉCNICA: Al final de tu respuesta de cierre, añade exactamente: CLAVE_ORDEN: [diagnóstico breve]."""
                        },
                        *st.session_state.messages
                    ],
                    model="llama-3.3-70b-versatile",
                )
                res = chat_completion.choices[0].message.content
                st.markdown(res)
                st.session_state.messages.append({"role": "assistant", "content": res})

                # Captura automática de la orden para el Área Administrativa
                if "CLAVE_ORDEN:" in res:
                    st.session_state.diagnostico_nexo = res.split("CLAVE_ORDEN:")[-1].strip()
                    st.session_state.orden_lista = True

            except Exception as e:
                st.error(f"Error de comunicación con el núcleo Nexo: {e}")

# --- MÓDULO: ÁREA ADMINISTRATIVA (Sustituye a Pasarela de Pago) ---
elif menu == "🏢 Área Administrativa":
    st.title("🏢 Registro y Formalización de Ingreso")
    st.caption("Dirección Administrativa - Instituto Clínico de Neuroprogramación AETHON")

    # 1. CEREBRO FINANCIERO (Triangulación USD -> EUR -> BS)
    @st.cache_data(ttl=3600)
    def calcular_montos_reales():
        tasa_euro_bcv = 360.50  # Tasa oficial según el BCV
        paridad_eur_usd = 0.92  # Paridad internacional (1 USD = 0.92 EUR)
        monto_usd = 80.00
        monto_eur = monto_usd * paridad_eur_usd
        monto_bs = monto_eur * tasa_euro_bcv
        return tasa_euro_bcv, monto_eur, monto_bs

    # Activamos los cálculos financieros
    tasa_bcv, total_eur, total_bs = calcular_montos_reales()

    if "orden_lista" in st.session_state and st.session_state.orden_lista:
        diag = st.session_state.get('diagnostico_nexo', 'Evaluación General')
        
        # 2. FICHA DE REGISTRO CLÍNICO (Estética de expediente)
        st.markdown(f"""
        <div style="background-color: #F0F2F6; padding: 25px; border-radius: 15px; border: 1px solid #1E3A8A;">
            <h4 style="color: #1E3A8A; margin-top:0; border-bottom: 2px solid #1E3A8A; padding-bottom: 10px;">📋 EXPEDIENTE DE INGRESO DIGITAL</h4>
            <p style="color: #000; margin-top:15px;"><strong>Protocolo Detectado:</strong> {diag}</p>
            <p style="color: #000;"><strong>Plan Asignado:</strong> Intervención Profunda (4 Sesiones)</p>
            <p style="color: #000;"><strong>Estatus Administrativo:</strong> Esperando formalización de honorarios</p>
            
            <div style="background-color: #1E3A8A; padding: 15px; border-radius: 8px; margin-top: 20px;">
                <p style="margin:0; font-weight: bold; color: #FFFFFF; font-size: 0.9rem;">VALORACIÓN SEGÚN TASA OFICIAL EUR (BCV):</p>
                <p style="margin:0; font-size: 1.3rem; color: #FFFFFF;">{tasa_bcv:.2f} Bs/EUR</p>
                <p style="margin:5px 0 0 0; font-weight: bold; color: #FFD700; font-size: 1.4rem;">MONTO DE FORMALIZACIÓN: {total_bs:,.2f} Bs.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("---")
        st.markdown("#### Seleccione su método de formalización:")
        
        # 3. MÉTODOS DE TRANSFERENCIA INSTITUCIONAL
        tab1, tab2 = st.tabs(["🇻🇪 PAGO MÓVIL (Mercantil)", "💎 DEPÓSITO DIGITAL (USDT)"])
        
        with tab1:
            st.markdown(f"""
            <div style="background-color: #FFFFFF; padding: 20px; border-radius: 10px; border: 1px solid #dee2e6;">
                <h5 style="color: #1E3A8A;">Datos para la transferencia administrativa:</h5>
                <p style="color: #000; margin: 5px 0;"><strong>Banco:</strong> Banco Mercantil</p>
                <p style="color: #000; margin: 5px 0;"><strong>Titular/RIF:</strong> V-15.214.337</p>
                <p style="color: #000; margin: 5px 0;"><strong>Teléfono:</strong> 04262272765</p>
                <div style="background-color: #f8f9fa; padding: 10px; border-left: 4px solid #1E3A8A; margin-top:10px;">
                    <p style="color: #1E3A8A; font-weight: bold; margin:0;">Monto exacto a transferir: {total_bs:,.2f} Bs.</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with tab2:
            st.info("Para transferencias internacionales vía USDT, utilice la red BEP20 (Binance Smart Chain).")
            st.code("0xE30516Af847E0a7E343917e0C204E1e974754dBa", language="text")
            st.caption("Copie la dirección para asegurar la integridad de la transacción.")

        st.write("---")
        
        # 4. REGISTRO DE REFERENCIA Y NOTIFICACIÓN
        st.subheader("Confirmación de Proceso")
        ref_bancaria = st.text_input("Ingrese el número de referencia de su transacción:", key="ref_admin")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 FINALIZAR REGISTRO CLÍNICO", use_container_width=True):
                if ref_bancaria:
                    st.balloons()
                    st.success("Registro administrativo completado con éxito. Su especialista será asignado en breve.")
                else:
                    st.error("Por favor, ingrese el número de referencia para procesar su ingreso.")
        
        with col2:
            # Mensaje institucional para WhatsApp
            texto_wa = f"Saludos Instituto AETHON. Formalizo mi ingreso administrativo. Referencia: {ref_bancaria}. Monto: {total_bs:,.2f} Bs."
            url_wa = f"https://wa.me/584262272765?text={texto_wa.replace(' ', '%20')}"
            st.link_button("💬 NOTIFICAR AL DEPARTAMENTO", url_wa, use_container_width=True)
            
    else:
        # Mensaje sutil si no han pasado por Nexo
        st.warning("⚠️ El acceso al Área Administrativa requiere la validación previa de su reporte clínico por Nexo.")
        st.info("Por favor, diríjase a la sección 'Consulta Médica' para iniciar su evaluación.")
        
