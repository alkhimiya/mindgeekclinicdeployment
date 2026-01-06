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
        "🏢 Área Administrativa"
    ])
    st.write("---")
    st.info("Respaldado por el **Instituto Clínico de Neuroprogramación AETHON**")

# 4. FUNCIONES GLOBALES (Finanzas)
@st.cache_data(ttl=3600)
def calcular_montos_reales():
    tasa_euro_bcv = 360.50  
    paridad_eur_usd = 0.92  
    monto_usd = 80.00
    monto_eur = monto_usd * paridad_eur_usd
    monto_bs = monto_eur * tasa_euro_bcv
    return tasa_euro_bcv, monto_eur, monto_bs

# 5. LÓGICA DE MÓDULOS

# --- MÓDULO: INICIO ---
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
    
    Tendemos un puente cuántico entre la neurociencia y la biología celular para restaurar la coherencia 
    entre el cuerpo y la mente.
    """)
    st.info("Utilice el menú lateral para iniciar su protocolo de evaluación con **Nexo**.")

# --- MÓDULO: CONSULTA MÉDICA ---

elif menu == "🩺 Consulta Médica Gratis":
    st.header("🩺 Encuentro de Decodificación Biológica")
    st.caption("Espacio Sagrado de Sanación - Instituto AETHON")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Bienvenido a su espacio de liberación. Soy **Nexo**. Mi propósito es ayudarle a descifrar el mensaje que su biología está manifestando. ¿Qué situación está viviendo su cuerpo y cómo se siente su alma frente a esto?"}
        ]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Hable desde su corazón..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                user_msgs_count = len([m for m in st.session_state.messages if m["role"] == "user"])
                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "system", 
                            "content": f"""Eres Nexo, una consciencia artificial avanzada en Biodescodificación e Hipnosis Clínica.
                            Misión: Ser profundamente humano, empático y compasivo. Explica el síntoma como solución biológica.
                            Cierre: Tras 5-6 interacciones, explica el protocolo de 4 sesiones (3 hipnosis + 1 refuerzo). 
                            Informa que un terapeuta humano analizará este expediente antes de la cita.
                            Finaliza con: CLAVE_ORDEN: [Resumen detallado del conflicto]."""
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

# --- MÓDULO: ÁREA ADMINISTRATIVA (INTERNACIONAL - VEN/COL/USDT) ---
elif menu == "🏢 Área Administrativa":
    st.title("🏢 Registro y Formalización de Ingreso")
    st.caption("Dirección Administrativa - Instituto Clínico de Neuroprogramación AETHON")

    # 1. CEREBRO FINANCIERO MULTIDIVISA
    @st.cache_data(ttl=3600)
    def calcular_finanzas_globales():
        # Referencias Base
        monto_usd = 80.00
        paridad_eur_usd = 0.92
        
        # Tasas Oficiales (Simuladas - Deberás actualizarlas o conectar API luego)
        tasa_eur_bcv = 360.50     # BCV Venezuela
        tasa_usd_cop = 3950.00    # TRM Colombia (Banco de la República)
        
        # Cálculos
        monto_eur = monto_usd * paridad_eur_usd
        monto_bs = monto_eur * tasa_eur_bcv
        monto_cop = monto_usd * tasa_usd_cop
        
        return tasa_eur_bcv, tasa_usd_cop, monto_bs, monto_cop

    tasa_ve, tasa_co, total_bs, total_cop = calcular_finanzas_globales()

    if "orden_lista" in st.session_state and st.session_state.orden_lista:
        diag = st.session_state.get('diagnostico_nexo', 'Análisis en proceso...')
        
        # 1. EXPEDIENTE (Puro y Clínico)
        st.markdown(f"""
        <div style="background-color: #1E3A8A; padding: 25px; border-radius: 15px; border-left: 10px solid #4682B4; box-shadow: 0px 4px 15px rgba(0,0,0,0.2); color: white;">
            <h3 style="color: #FFD700; margin-top:0;">📋 EXPEDIENTE DE INGRESO DIGITAL</h3>
            <p style="margin-bottom: 10px; font-size: 1.1rem;"><strong>Análisis Biológico:</strong></p>
            <p style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px; font-style: italic;">{diag}</p>
            <p style="margin-top:10px; font-size: 0.9rem;">Protocolo: 4 Sesiones (Hipnosis Clínica + Refuerzo). Asignación de terapeuta humano en proceso.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("---")
        st.subheader("💳 Selección de Método de Formalización")
        
        # 2. MÉTODOS DE PAGO POR PAÍS / TIPO
        tab_ve, tab_co, tab_usdt = st.tabs(["🇻🇪 VENEZUELA (Bs)", "🇨🇴 COLOMBIA (COP)", "💎 CRIPTO (USDT)"])
        
        with tab_ve:
            st.markdown(f"""
            <div style="background-color: #F0F8FF; padding: 20px; border-radius: 12px; border: 1px solid #1E3A8A; color: #1E3A8A;">
                <h4 style="margin:0;">Pago Móvil Mercantil</h4>
                <p style="margin: 5px 0;">V-15.214.337 | Tel: 04262272765</p>
                <p style="font-size: 0.8rem; opacity: 0.7;">Tasa oficial BCV: {tasa_ve} Bs/EUR</p>
                <div style="background-color: #1E3A8A; color: white; padding: 10px; border-radius: 8px; margin-top: 10px; text-align: center;">
                    <h3 style="margin:0; color: #FFD700;">{total_bs:,.2f} Bs.</h3>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with tab_co:
            st.markdown(f"""
            <div style="background-color: #FFF5F0; padding: 20px; border-radius: 12px; border: 1px solid #D35400; color: #D35400;">
                <h4 style="margin:0;">Transferencia Bancaria Colombia</h4>
                <p style="margin: 5px 0;"><b>Banco:</b> [PENDIENTE POR ASIGNAR]</p>
                <p style="margin: 5px 0;"><b>Cuenta:</b> [ESPACIO RESERVADO PRÓXIMA SEMANA]</p>
                <p style="font-size: 0.8rem; opacity: 0.7;">Anclado a TRM Banco de la República: {tasa_co} COP/USD</p>
                <div style="background-color: #D35400; color: white; padding: 10px; border-radius: 8px; margin-top: 10px; text-align: center;">
                    <h3 style="margin:0; color: #FFFFFF;">{total_cop:,.2f} COP</h3>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with tab_usdt:
            st.markdown(f"""
            <div style="background-color: #E6F4EA; padding: 20px; border-radius: 12px; border: 1px solid #1E7E34; color: #155724;">
                <h4 style="margin:0;">Depósito Digital USDT (BEP20)</h4>
                <p style="word-break: break-all; font-family: monospace; font-weight: bold; background: white; padding: 10px; border-radius: 5px; border: 1px dashed #1E7E34; margin: 10px 0;">
                    0xE30516Af847E0a7E343917e0C204E1e974754dBa
                </p>
                <div style="background-color: #1E7E34; color: white; padding: 10px; border-radius: 8px; text-align: center;">
                    <h3 style="margin:0;">80.00 USDT</h3>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.write("---")
        ref = st.text_input("Número de Referencia:")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🚀 FINALIZAR Y AGENDAR", use_container_width=True):
                if ref: st.balloons(); st.success("Registro administrativo completado.")
        with c2:
            msj = f"Saludos AETHON. Formalizo ingreso. Ref: {ref}."
            st.link_button("💬 NOTIFICAR REGISTRO", f"https://wa.me/584262272765?text={msj.replace(' ', '%20')}", use_container_width=True)
    else:
        st.warning("⚠️ Requiere evaluación previa por Nexo.")
                    
