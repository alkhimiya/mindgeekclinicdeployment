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
                    st.session_state.orden_lista = True
            except Exception as e:
                st.error(f"Error de conexión con Nexo: {e}")

# --- MÓDULO: ÁREA ADMINISTRATIVA ---
elif menu == "🏢 Área Administrativa":
    st.title("🏢 Registro y Formalización de Ingreso")
    st.caption("Instituto Clínico de Neuroprogramación AETHON")

    tasa_bcv, total_eur, total_bs = calcular_montos_reales()

    if "orden_lista" in st.session_state and st.session_state.orden_lista:
        diag = st.session_state.get('diagnostico_nexo', 'Evaluación General')
        
        # Expediente Premium Tech
        st.markdown(f"""
        <div style="background-color: #1E3A8A; padding: 25px; border-radius: 15px; border-left: 10px solid #4682B4; box-shadow: 0px 4px 15px rgba(0,0,0,0.2); color: white;">
            <h3 style="color: #FFD700; margin-top:0;">📋 EXPEDIENTE DE INGRESO DIGITAL</h3>
            <p style="margin-bottom: 10px; font-size: 1.1rem;"><strong>Análisis de Raíz:</strong> {diag}</p>
            <p style="font-size: 0.9rem; color: #4682B4;">Protocolo: 3 Sesiones Hipnosis + 1 Refuerzo. <i>Un terapeuta humano estudiará este caso previo a su cita.</i></p>
            <hr style="border: 0.5px solid rgba(255,255,255,0.2);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div><p style="margin:0; opacity: 0.8;">Inversión</p><p style="margin:0; font-size: 1.4rem; font-weight: bold;">$80.00 USD</p></div>
                <div style="text-align: right;"><p style="margin:0; opacity: 0.8;">Tasa BCV</p><p style="margin:0; font-size: 1.4rem; font-weight: bold;">{tasa_bcv} Bs.</p></div>
            </div>
            <div style="background-color: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; margin-top: 15px; text-align: center; border: 1px solid #FFD700;">
                <h2 style="margin:0; color: #FFFFFF;">{total_bs:,.2f} <span style="font-size: 1.2rem;">Bs.</span></h2>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("---")
        tab1, tab2 = st.tabs(["🇻🇪 PAGO MÓVIL", "💎 BILLETERA USDT"])
        
        with tab1:
            st.markdown(f"""<div style="background-color: #F0F8FF; padding: 20px; border-radius: 12px; border: 1px solid #1E3A8A; color: #1E3A8A;">
                <h4 style="margin:0;">Datos Mercantil:</h4>
                V-15.214.337 | 04262272765 | <b>Monto: {total_bs:,.2f} Bs.</b></div>""", unsafe_allow_html=True)

        with tab2:
            st.markdown(f"""<div style="background-color: #E6F4EA; padding: 20px; border-radius: 12px; border: 1px solid #1E7E34; color: #155724;">
                <h4 style="margin:0;">Red BEP20:</h4>
                <p style="word-break: break-all; font-family: monospace;">0xE30516Af847E0a7E343917e0C204E1e974754dBa</p></div>""", unsafe_allow_html=True)

        st.write("---")
        ref = st.text_input("Referencia de pago:")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🚀 FINALIZAR REGISTRO CLÍNICO", use_container_width=True):
                if ref: st.balloons(); st.success("¡Bienvenido al Instituto AETHON!")
        with c2:
            msj = f"Saludos AETHON. Formalizo mi ingreso. Ref: {ref}. Monto: {total_bs:,.2f} Bs."
            st.link_button("💬 NOTIFICAR REGISTRO", f"https://wa.me/584262272765?text={msj.replace(' ', '%20')}", use_container_width=True)
    else:
        st.warning("⚠️ Requiere evaluación previa por Nexo.")

