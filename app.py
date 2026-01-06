import streamlit as st
import os
from groq import Groq

# 1. CONFIGURACIÓN INICIAL Y ESTILO PREMIUM
st.set_page_config(page_title="MIND GEEK CLINIC", layout="wide", page_icon="🧠")

st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #1E3A8A; color: white; }
    .titulo-principal { font-size: 3rem !important; font-weight: 800; color: #1E3A8A; line-height: 1; margin-bottom: 0; }
    .subtitulo-vanguardia { font-size: 1.5rem !important; color: #4682B4 !important; font-weight: 500; font-style: italic; margin-top: 0; }
    .stChatFloatingInputContainer { bottom: 20px; }
    .monto-grande { font-size: 2.2rem !important; font-weight: 800; color: #FFD700; margin: 0; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXIÓN IA
try:
    client = Groq(api_key=st.secrets["groq"]["api_key"])
    CONEXION_IA = True
except Exception as e:
    CONEXION_IA = False

# 3. SIDEBAR
with st.sidebar:
    st.title("🧠 MIND GEEK CLINIC")
    st.write("---")
    menu = st.radio("Navegación", ["🏠 Inicio", "🩺 Consulta Médica Gratis", "🏢 Área Administrativa"])
    st.write("---")
    st.info("Respaldado por el **Instituto Clínico de Neuroprogramación AETHON**")

# 4. MOTOR FINANCIERO (Triangulación)
@st.cache_data(ttl=3600)
def calcular_finanzas():
    m_usd = 80.00
    p_eur = 0.92
    t_ve = 360.50     
    t_co = 3950.00    
    m_bs = (m_usd * p_eur) * t_ve
    m_cop = m_usd * t_co
    return t_ve, t_co, m_bs, m_cop

tasa_ve, tasa_co, total_bs, total_cop = calcular_finanzas()

# 5. MÓDULOS

# --- INICIO: IDENTIDAD HEALTHTECH ---
if menu == "🏠 Inicio":
    st.markdown('<h1 class="titulo-principal">MIND GEEK CLINIC</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitulo-vanguardia">La Vanguardia en Salud Mental & Biodescodificación</p>', unsafe_allow_html=True)
    st.write("---")
    st.markdown("""
    ### **La Frontera de la Nueva Medicina**
    Bienvenido a una experiencia donde la **computación avanzada** y la **inteligencia del alma** convergen. En **Mind Geek Clinic**, somos una *HealthTech* pionera que integra la Biodescodificación Cuántica con tecnología de punta para decodificar los síntomas biológicos y transformarlos en caminos de sanación integral.
    
    Nuestro sistema **Nexo** analiza la raíz emocional de su síntoma, preparando el terreno para una intervención profunda con nuestros especialistas humanos.
    """)
    st.info("Inicie su protocolo de evaluación con **Nexo** en el menú lateral.")

# --- CONSULTA: NEXO EMPÁTICO ---
elif menu == "🩺 Consulta Médica Gratis":
    st.header("🩺 Encuentro de Decodificación Biológica")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Bienvenido. Soy **Nexo**. Mi propósito es ayudarle a descifrar el mensaje que su biología está manifestando. ¿Qué situación vive su cuerpo y cómo se siente su alma?"}]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]): st.markdown(message["content"])

    if prompt := st.chat_input("Hable desde su corazón..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                # Lógica interna de conteo (invisible para el usuario)
                u_turns = len([m for m in st.session_state.messages if m["role"] == "user"])
                
                chat_completion = client.chat.completions.create(
                    messages=[{
                        "role": "system", 
                        "content": f"""Eres Nexo de AETHON. Eres un Biodescodificador empático y profundo.
                        TU MISIÓN: Escuchar y analizar. NO menciones pasos ni números de mensajes al paciente.
                        REGLA DE CIERRE: Solo si detectas que el paciente está listo y llevas al menos 5 turnos (llevas {u_turns}), invítalo con calidez al Área Administrativa para formalizar su ingreso y que un terapeuta humano reciba su expediente.
                        Finaliza con: CLAVE_ORDEN: [Resumen clínico]."""
                    }] + st.session_state.messages,
                    model="llama-3.3-70b-versatile",
                )
                res = chat_completion.choices[0].message.content
                st.markdown(res)
                st.session_state.messages.append({"role": "assistant", "content": res})
                if "CLAVE_ORDEN:" in res and u_turns >= 5:
                    st.session_state.diagnostico_nexo = res.split("CLAVE_ORDEN:")[-1].strip()
                    st.session_state.orden_lista = True
            except Exception as e: st.error(f"Error: {e}")

# --- ADMINISTRACIÓN: DISEÑO PREMIUM ---
elif menu == "🏢 Área Administrativa":
    st.title("🏢 Registro y Formalización")
    if "orden_lista" in st.session_state:
        # EXPEDIENTE PROFESIONAL
        st.markdown(f"""
        <div style="background-color: #1E3A8A; padding: 30px; border-radius: 15px; color: white; border-left: 12px solid #4682B4; box-shadow: 0px 10px 30px rgba(0,0,0,0.3);">
            <h2 style="color: #FFD700; margin-top:0;">📋 EXPEDIENTE DIGITAL</h2>
            <p style="font-style: italic; font-size: 1.2rem; line-height: 1.6;">{st.session_state.diagnostico_nexo}</p>
            <p style="font-size: 0.9rem; opacity: 0.8; margin-top:20px;">Protocolo: 4 Sesiones. Este informe será auditado por el especialista asignado.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("---")
        t_ve, t_co, m_bs, m_cop = calcular_finanzas()
        
        tab_ve, tab_co, tab_usdt = st.tabs(["🇻🇪 VENEZUELA", "🇨🇴 COLOMBIA", "💎 CRIPTO"])
        
        with tab_ve:
            st.markdown(f"""<div style="background:#F0F8FF; padding:25px; border-radius:15px; border:2px solid #1E3A8A; text-align:center;">
                <h3 style="color:#1E3A8A; margin:0;">Pago Móvil Mercantil</h3>
                <p style="color:#1E3A8A;">V-15.214.337 | 04262272765</p>
                <div style="background:#1E3A8A; padding:15px; border-radius:10px; margin-top:15px;">
                    <p style="color:white; margin:0; font-size:1rem;">MONTO TOTAL A TRANSFERIR:</p>
                    <p class="monto-grande">{m_bs:,.2f} Bs.</p>
                </div></div>""", unsafe_allow_html=True)

        with tab_co:
            st.markdown(f"""<div style="background:#FFF5F0; padding:25px; border-radius:15px; border:2px solid #D35400; text-align:center;">
                <h3 style="color:#D35400; margin:0;">Transferencia Bancaria</h3>
                <p style="color:#D35400;">[Cuenta por asignar la próxima semana]</p>
                <div style="background:#D35400; padding:15px; border-radius:10px; margin-top:15px;">
                    <p style="color:white; margin:0; font-size:1rem;">MONTO TOTAL A TRANSFERIR:</p>
                    <p class="monto-grande">{m_cop:,.2f} COP</p>
                </div></div>""", unsafe_allow_html=True)

        with tab_usdt:
            st.markdown(f"""<div style="background:#E6F4EA; padding:25px; border-radius:15px; border:2px solid #1E7E34; text-align:center;">
                <h3 style="color:#1E7E34; margin:0;">USDT (Red BEP20)</h3>
                <p style="color:#1E7E34; word-break: break-all;">0xE30516Af847E0a7E343917e0C204E1e974754dBa</p>
                <div style="background:#1E7E34; padding:15px; border-radius:10px; margin-top:15px;">
                    <p style="color:white; margin:0; font-size:1rem;">INVERSIÓN DIGITAL:</p>
                    <p class="monto-grande">80.00 USDT</p>
                </div></div>""", unsafe_allow_html=True)

        ref = st.text_input("Número de Referencia:")
        if st.button("🚀 FINALIZAR Y AGENDAR"):
            if ref: st.balloons(); st.success("¡Ingreso validado!")
    else:
        st.warning("⚠️ Su expediente aún no ha sido generado por Nexo.")
        
