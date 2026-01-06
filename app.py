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

# --- MÓDULO: ÁREA ADMINISTRATIVA (DISEÑO PREMIUM TECH REFORZADO) ---
elif menu == "🏢 Área Administrativa":
    st.title("🏢 Registro y Formalización de Ingreso")
    st.caption("Instituto Clínico de Neuroprogramación AETHON")

    # 1. CEREBRO FINANCIERO
    @st.cache_data(ttl=3600)
    def calcular_montos_reales():
        tasa_euro_bcv = 360.50  
        paridad_eur_usd = 0.92  
        monto_usd = 80.00
        monto_eur = monto_usd * paridad_eur_usd
        monto_bs = monto_eur * tasa_euro_bcv
        return tasa_euro_bcv, monto_eur, monto_bs

    tasa_bcv, total_eur, total_bs = calcular_montos_reales()

    if "orden_lista" in st.session_state and st.session_state.orden_lista:
        diag = st.session_state.get('diagnostico_nexo', 'Evaluación General')
        
        # 2. EXPEDIENTE DIGITAL COLORIDO (Diseño de Alto Impacto)
        st.markdown(f"""
        <div style="background-color: #1E3A8A; padding: 25px; border-radius: 15px; border-left: 10px solid #4682B4; box-shadow: 0px 4px 15px rgba(0,0,0,0.2); color: white;">
            <h3 style="color: #FFD700; margin-top:0;">📋 EXPEDIENTE DE INGRESO DIGITAL</h3>
            <p style="margin-bottom: 10px; font-size: 1.1rem;"><strong>Protocolo Detectado:</strong> {diag}</p>
            <hr style="border: 0.5px solid rgba(255,255,255,0.2);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <p style="margin:0; font-size: 0.9rem; opacity: 0.8;">Inversión Base</p>
                    <p style="margin:0; font-size: 1.4rem; font-weight: bold;">$80.00 USD</p>
                </div>
                <div style="text-align: right;">
                    <p style="margin:0; font-size: 0.9rem; opacity: 0.8;">Tasa EUR (BCV)</p>
                    <p style="margin:0; font-size: 1.4rem; font-weight: bold;">{tasa_bcv} Bs.</p>
                </div>
            </div>
            <div style="background-color: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; margin-top: 15px; text-align: center; border: 1px solid #FFD700;">
                <p style="margin:0; font-size: 1rem; color: #FFD700; font-weight: bold;">TOTAL A FORMALIZAR:</p>
                <h2 style="margin:0; font-size: 2.2rem; color: #FFFFFF;">{total_bs:,.2f} <span style="font-size: 1.2rem;">Bs.</span></h2>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("---")
        
        # 3. MÉTODOS DE PAGO CON COLOR
        tab1, tab2 = st.tabs(["🇻🇪 PAGO MÓVIL (MERCANTIL)", "💎 BILLETERA USDT"])
        
        with tab1:
            st.markdown(f"""
            <div style="background-color: #F0F8FF; padding: 20px; border-radius: 12px; border: 1px solid #1E3A8A; color: #1E3A8A;">
                <h4 style="margin-top:0; color: #1E3A8A;">Datos de Transferencia:</h4>
                <p style="margin: 5px 0;"><strong>Banco:</strong> Banco Mercantil</p>
                <p style="margin: 5px 0;"><strong>Cédula:</strong> V-15.214.337</p>
                <p style="margin: 5px 0;"><strong>Teléfono:</strong> 04262272765</p>
                <p style="margin-top: 10px; font-size: 1.2rem; font-weight: bold; background: #1E3A8A; color: white; padding: 5px 10px; border-radius: 5px; display: inline-block;">
                    Monto: {total_bs:,.2f} Bs.
                </p>
            </div>
            """, unsafe_allow_html=True)

        with tab2:
            st.markdown(f"""
            <div style="background-color: #E6F4EA; padding: 20px; border-radius: 12px; border: 1px solid #1E7E34; color: #155724;">
                <h4 style="margin-top:0; color: #155724;">Dirección USDT (Red BEP20):</h4>
                <p style="word-break: break-all; font-family: monospace; font-size: 1.1rem; font-weight: bold; background: white; padding: 10px; border-radius: 5px; border: 1px dashed #1E7E34;">
                    0xE30516Af847E0a7E343917e0C204E1e974754dBa
                </p>
                <p style="font-size: 0.8rem; margin-top: 5px;">⚠️ Asegúrese de utilizar únicamente la red Binance Smart Chain.</p>
            </div>
            """, unsafe_allow_html=True)

        st.write("---")
        
        # 4. REGISTRO Y WHATSAPP
        ref = st.text_input("Número de Referencia:")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🚀 FINALIZAR REGISTRO CLÍNICO", use_container_width=True):
                if ref: st.balloons(); st.success("¡Registro Exitoso!")
        with c2:
            msj = f"Saludos Instituto AETHON. Formalizo mi ingreso. Ref: {ref}. Monto: {total_bs:,.2f} Bs."
            st.link_button("💬 NOTIFICAR AL DEPARTAMENTO", f"https://wa.me/584262272765?text={msj.replace(' ', '%20')}", use_container_width=True)
            
    else:
        st.warning("⚠️ Su reporte clínico requiere validación de Nexo.")
        
            
        
