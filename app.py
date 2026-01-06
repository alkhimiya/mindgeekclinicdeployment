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

# --- MÓDULO: ÁREA ADMINISTRATIVA (DISEÑO BLINDADO DE ALTO CONTRASTE) ---
elif menu == "🏢 Área Administrativa":
    st.title("🏢 Registro y Formalización")
    st.markdown("### Instituto Clínico de Neuroprogramación AETHON")
    st.divider()

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
        
        # 2. EXPEDIENTE (Usando columnas y contenedores nativos)
        with st.container(border=True):
            st.subheader("📋 Expediente de Ingreso Digital")
            
            c1, c2 = st.columns(2)
            c1.markdown(f"**Protocolo:** \n {diag}")
            c2.markdown(f"**Plan:** \n Intervención Profunda (4 Sesiones)")
            
            st.divider()
            
            # Métricas grandes y claras (Estas nunca fallan visualmente)
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Inversión Base", "$80.00 USD")
            col_b.metric("Tasa EUR/BS (BCV)", f"{tasa_bcv}")
            col_c.metric("Total a Formalizar", f"{total_bs:,.2f} Bs.")
            
            st.info(f"Monto exacto a transferir: {total_bs:,.2f} Bolívares")

        st.write("---")
        
        # 3. DATOS DE TRANSFERENCIA (Formato simple y legible)
        st.markdown("#### 💳 Métodos de Transferencia")
        
        pago_movil, usdt = st.tabs(["🇻🇪 Pago Móvil Mercantil", "💎 Cripto USDT"])
        
        with pago_movil:
            # Usamos un bloque de código para los datos, así se ven destacados en gris
            st.markdown("**Envíe su transferencia con los siguientes datos:**")
            st.code(f"""
Banco: Mercantil
Cédula: V-15.214.337
Teléfono: 04262272765
Monto: {total_bs:,.2f} Bs.
            """, language="text")
            st.caption("Verifique los datos antes de confirmar.")

        with usdt:
            st.write("Red: **Binance Smart Chain (BEP20)**")
            st.code("0xE30516Af847E0a7E343917e0C204E1e974754dBa", language="text")

        st.write("---")
        
        # 4. FORMULARIO DE CIERRE
        st.subheader("Confirmación de Proceso")
        ref = st.text_input("Número de Referencia Bancaria:", placeholder="Ej: 002345...")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🚀 FINALIZAR REGISTRO", use_container_width=True, type="primary"):
                if ref:
                    st.balloons()
                    st.success("Registro completado. Bienvenido al Instituto AETHON.")
                else:
                    st.error("Por favor, escriba la referencia.")
        
        with col_btn2:
            msj = f"Saludos Instituto AETHON. Formalizo mi ingreso. Ref: {ref}. Monto: {total_bs:,.2f} Bs."
            st.link_button("💬 NOTIFICAR POR WHATSAPP", f"https://wa.me/584262272765?text={msj.replace(' ', '%20')}", use_container_width=True)
            
    else:
        st.warning("⚠️ Se requiere la validación clínica de Nexo para acceder a esta área.")
            
        
