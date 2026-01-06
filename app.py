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
    menu = st.radio("Navegación", ["🏠 Inicio", "🩺 Consulta Médica Gratis", "🏢 Área Administrativa"])
    st.write("---")
    st.info("Respaldado por el **Instituto Clínico de Neuroprogramación AETHON**")

# 4. FUNCIONES GLOBALES (Cerebro Financiero)
@st.cache_data(ttl=3600)
def calcular_finanzas_globales():
    monto_usd = 80.00
    paridad_eur_usd = 0.92
    tasa_ve_bcv = 360.50     # Euro BCV
    tasa_co_trm = 3950.00    # TRM Colombia aprox.
    
    monto_eur = monto_usd * paridad_eur_usd
    monto_bs = monto_eur * tasa_ve_bcv
    monto_cop = monto_usd * tasa_co_trm
    
    return tasa_ve_bcv, tasa_co_trm, monto_bs, monto_cop

tasa_ve, tasa_co, total_bs, total_cop = calcular_finanzas_globales()

# 5. LÓGICA DE MÓDULOS

# --- MÓDULO: INICIO ---
if menu == "🏠 Inicio":
    st.markdown('<h1 class="titulo-principal">Bienvenidos a <br>Mind Geek Clinic</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitulo-vanguardia">La vanguardia en salud mental</p>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("""
    #### **La Frontera de la Nueva Medicina**
    Bienvenidos a la intersección donde la computación avanzada se encuentra con la inteligencia del alma. 
    Hemos decodificado el lenguaje del síntoma para ofrecerle un puente cuántico hacia su sanación.
    """)
    st.info("Inicie su protocolo de evaluación con **Nexo** en el menú lateral.")

# --- MÓDULO: CONSULTA MÉDICA (NEXO) ---
elif menu == "🩺 Consulta Médica Gratis":
    st.header("🩺 Encuentro de Decodificación Biológica")
    st.caption("Interacción profunda con Nexo - Instituto AETHON")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Bienvenido. Soy **Nexo**. Mi propósito es ayudarle a descifrar el mensaje que su biología está manifestando. ¿Qué situación vive su cuerpo y cómo se siente su alma?"}]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Hable desde su corazón..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                chat_completion = client.chat.completions.create(
                    messages=[{
                        "role": "system", 
                        "content": "Eres Nexo, experto en Biodescodificación e Hipnosis. Tu tono es extremadamente empático y humano. Explica que la enfermedad es una respuesta biológica a un conflicto emocional. Debes indagar profundamente (5-6 turnos). Al final, ofrece el protocolo de 4 sesiones (3 hipnosis + 1 refuerzo) y menciona que un especialista humano analizará este expediente antes de la cita presencial/online. Finaliza con: CLAVE_ORDEN: [Resumen]."
                    }] + st.session_state.messages,
                    model="llama-3.3-70b-versatile",
                )
                res = chat_completion.choices[0].message.content
                st.markdown(res)
                st.session_state.messages.append({"role": "assistant", "content": res})

                if "CLAVE_ORDEN:" in res:
                    st.session_state.diagnostico_nexo = res.split("CLAVE_ORDEN:")[-1].strip()
                    st.session_state.orden_lista = True
            except Exception as e:
                st.error(f"Error de comunicación con el núcleo: {e}")

# --- MÓDULO: ÁREA ADMINISTRATIVA ---
elif menu == "🏢 Área Administrativa":
    st.title("🏢 Registro y Formalización de Ingreso")
    
    if "orden_lista" in st.session_state and st.session_state.orden_lista:
        diag = st.session_state.get('diagnostico_nexo', 'Evaluación en proceso')
        
        # 1. EXPEDIENTE (Elegancia Clínica sin montos)
        st.markdown(f"""
        <div style="background-color: #1E3A8A; padding: 25px; border-radius: 15px; color: white; border-left: 10px solid #4682B4; box-shadow: 0px 4px 15px rgba(0,0,0,0.2);">
            <h3 style="color: #FFD700; margin-top:0;">📋 EXPEDIENTE DE INGRESO DIGITAL</h3>
            <p style="font-style: italic; margin-top:10px; line-height: 1.6;">{diag}</p>
            <hr style="border: 0.5px solid rgba(255,255,255,0.2);">
            <p style="font-size: 0.9rem;"><b>Protocolo:</b> 4 Sesiones de Intervención Profunda. Un terapeuta humano estudiará este análisis para abordar su cita con total conocimiento de su caso.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("---")
        st.subheader("💳 Selección de Honorarios por País")
        tab_ve, tab_co, tab_usdt = st.tabs(["🇻🇪 VENEZUELA (Bs)", "🇨🇴 COLOMBIA (COP)", "💎 CRIPTO (USDT)"])
        
        with tab_ve:
            st.markdown(f"""<div style="background-color: #F0F8FF; padding: 20px; border-radius: 12px; border: 1px solid #1E3A8A;">
                <h4 style="color: #1E3A8A; margin:0;">Pago Móvil Mercantil</h4>
                <p style="color: #1E3A8A; margin: 5px 0;">V-15.214.337 | Tel: 04262272765 | Tasa BCV: {tasa_ve} Bs.</p>
                <div style="background: #1E3A8A; color: #FFD700; padding: 15px; border-radius: 8px; text-align: center; margin-top:10px;">
                <p style="margin:0; font-size: 0.8rem; color: white;">TOTAL A TRANSFERIR:</p>
                <h2 style="margin:0;">{total_bs:,.2f} Bs.</h2></div></div>""", unsafe_allow_html=True)

        with tab_co:
            st.markdown(f"""<div style="background-color: #FFF5F0; padding: 20px; border-radius: 12px; border: 1px solid #D35400;">
                <h4 style="color: #D35400; margin:0;">Transferencia Bancaria Colombia</h4>
                <p style="color: #D35400; margin: 5px 0;">Datos: [Cuenta por asignar la próxima semana] | TRM: {tasa_co} COP</p>
                <div style="background: #D35400; color: white; padding: 15px; border-radius: 8px; text-align: center; margin-top:10px;">
                <p style="margin:0; font-size: 0.8rem; opacity: 0.9;">TOTAL A TRANSFERIR:</p>
                <h2 style="margin:0;">{total_cop:,.2f} COP</h2></div></div>""", unsafe_allow_html=True)

        with tab_usdt:
            st.markdown(f"""<div style="background-color: #E6F4EA; padding: 20px; border-radius: 12px; border: 1px solid #1E7E34;">
                <h4 style="color: #1E7E34; margin:0;">USDT (Red BEP20)</h4>
                <p style="color: #1E7E34; word-break: break-all; font-family: monospace;">0xE30516Af847E0a7E343917e0C204E1e974754dBa</p>
                <div style="background: #1E7E34; color: white; padding: 15px; border-radius: 8px; text-align: center; margin-top:10px;">
                <p style="margin:0; font-size: 0.8rem; opacity: 0.9;">INVERSIÓN DIGITAL:</p>
                <h2 style="margin:0;">80.00 USDT</h2></div></div>""", unsafe_allow_html=True)

        st.write("---")
        ref = st.text_input("Número de Referencia de Pago:")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🚀 FINALIZAR Y AGENDAR CITA", use_container_width=True):
                if ref: st.balloons(); st.success("Registro administrativo exitoso. Su proceso ha comenzado.")
        with c2:
            msj = f"Saludos AETHON. Formalizo mi ingreso. Ref: {ref}."
            st.link_button("💬 NOTIFICAR REGISTRO POR WHATSAPP", f"https://wa.me/584262272765?text={msj.replace(' ', '%20')}", use_container_width=True)
    else:
        st.warning("⚠️ El Área Administrativa se habilitará una vez que Nexo complete su evaluación clínica.")
        
