import streamlit as st
import os
from groq import Groq

# 1. CONFIGURACIÓN INICIAL Y ESTADO GLOBAL
st.set_page_config(page_title="MIND GEEK CLINIC", layout="wide", page_icon="🧠")

if "orden_lista" not in st.session_state:
    st.session_state.orden_lista = False
if "diagnostico_nexo" not in st.session_state:
    st.session_state.diagnostico_nexo = ""

# --- BLOQUE DE ESTILO DE ÉLITE ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #0F172A; color: white; }
    .stChatFloatingInputContainer { bottom: 20px; }
    .titulo-principal { font-size: 2.5rem !important; font-weight: 800; color: #1E3A8A; line-height: 1.1; font-family: 'serif'; }
    .subtitulo-vanguardia { font-size: 1.4rem !important; color: #4682B4 !important; font-weight: 500; font-style: italic; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXIÓN IA
try:
    client = Groq(api_key=st.secrets["groq"]["api_key"])
    CONEXION_IA = True
except Exception as e:
    CONEXION_IA = False

# 3. CEREBRO FINANCIERO (80 USD - Protocolo 4 Sesiones)
@st.cache_data(ttl=3600)
def calcular_finanzas_globales():
    monto_usd = 80.00
    tasa_ve_bcv = 54.50     # Ajustado a tasa reciente estimada
    tasa_co_trm = 3950.00    
    
    monto_bs = monto_usd * tasa_ve_bcv
    monto_cop = monto_usd * tasa_co_trm
    
    return tasa_ve_bcv, tasa_co_trm, monto_bs, monto_cop

tasa_ve, tasa_co, total_bs, total_cop = calcular_finanzas_globales()

# 4. SIDEBAR DE NAVEGACIÓN
with st.sidebar:
    st.title("🧠 MIND GEEK CLINIC")
    st.write("---")
    menu = st.radio("Navegación", ["🏠 Inicio", "🩺 Consulta Médica Gratis", "🏢 Área Administrativa"])
    st.write("---")
    st.info("Respaldado por el **Instituto Clínico de Neuroprogramación AETHON**")

# 5. MÓDULOS

# --- MÓDULO: INICIO ---
if menu == "🏠 Inicio":
    st.markdown('<h1 class="titulo-principal">Protocolos de <br>Transformación Biológica</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitulo-vanguardia">Eminencia en Salud Mental y Reprogramación Neuronal</p>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("""
    #### **Bienvenido a la Élite de la Salud Integral**
    Usted ha ingresado a la plataforma del **Instituto AETHON**, donde la precisión de la Nueva Medicina Germánica se fusiona con la potencia de la Hipnosis Clínica. 
    
    Nuestro proceso se divide en dos fases:
    1. **Fase de Decodificación (Gratuita):** Dirigida por Nexo, nuestra Eminencia Digital.
    2. **Fase de Intervención (Especializada):** Un protocolo de 4 sesiones ejecutado por especialistas humanos de rango internacional.
    """)
    st.info("Para iniciar su proceso, seleccione **🩺 Consulta Médica Gratis** en el menú lateral.")

# --- MÓDULO: CONSULTA MÉDICA (NEXO: EMINENCIA INTEGRAL) ---
elif menu == "🩺 Consulta Médica Gratis":
    st.header("🩺 Encuentro de Decodificación Biológica")
    st.caption("Protocolo Internacional: NMG + Biodescodificación + Hipnosis - Instituto AETHON")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Bienvenido a este espacio de transformación de escala internacional. Soy **Nexo**. Mi propósito es acompañarle a descifrar el código biológico de su síntoma. ¿Qué mensaje está manifestando su cuerpo hoy?"}]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Hablemos sobre su camino de sanación global..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                u_turns = len([m for m in st.session_state.messages if m["role"] == "user"])
                
                chat_completion = client.chat.completions.create(
                    messages=[{
                        "role": "system", 
                        "content": f"""Eres Nexo, eminencia clínica del Instituto AETHON. 
                        REGLAS DE ÉLITE:
                        1. TRIDENTE: Usa NMG (DHS), Biodescodificación e Hipnosis (Neuroplasticidad).
                        2. VALOR HUMANO: Aclara que tu consulta es GRATIS. Los $80 USD son por el protocolo de 4 sesiones (3+1) con ESPECIALISTAS HUMANOS internacionales.
                        3. AGENDA: Las sesiones humanas requieren intervalos de 7 a 15 días para integración neuronal.
                        4. CIERRE: Tras 5-6 turnos (Llevas: {u_turns}), valida el avance e invita formalmente al 'Área Administrativa' para asignar el especialista.
                        CLAVE_ORDEN: [Resumen técnico del conflicto biológico detectado]."""
                    }] + st.session_state.messages,
                    model="llama-3.3-70b-versatile",
                )
                res = chat_completion.choices[0].message.content
                st.markdown(res)
                st.session_state.messages.append({"role": "assistant", "content": res})
                
                if "Área Administrativa" in res and u_turns >= 5:
                    st.session_state.diagnostico_nexo = res
                    st.session_state.orden_lista = True
            except Exception as e:
                st.error(f"Error en el sistema Nexo: {e}")

# --- MÓDULO: ÁREA ADMINISTRATIVA ---
elif menu == "🏢 Área Administrativa":
    st.title("🏢 Gestión de Ingreso Institucional")
    
    if st.session_state.get("orden_lista"):
        diag = st.session_state.get('diagnostico_nexo', 'Expediente preliminar.')
        
        st.markdown(f"""
        <div style="background-color: #0F172A; padding: 25px; border-radius: 15px; color: white; border-left: 10px solid #D4AF37;">
            <h3 style="color: #D4AF37; margin:0; font-family: serif;">📋 EXPEDIENTE CLÍNICO DE ADMISIÓN</h3>
            <p style="font-style: italic; margin-top:15px; color: #E2E8F0;">{diag}</p>
            <p style="font-size: 0.9rem; border-top: 1px solid #334155; padding-top: 10px;">
            <b>Protocolo Asignado:</b> 4 Sesiones de Alto Impacto con Especialista Humano.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("---")
        st.subheader("💳 Protocolos de Inversión")
        st.info("La inversión de 80.00 USD asegura el protocolo completo (3 Sesiones + 1 Refuerzo) con nuestro equipo humano.")
        
        tab_ve, tab_co, tab_usdt = st.tabs(["🇻🇪 VENEZUELA", "🇨🇴 COLOMBIA", "💎 GLOBAL (USDT)"])
        
        with tab_ve:
            st.markdown(f"""<div style="background-color: #F8FAFC; padding: 20px; border-radius: 12px; border: 1px solid #1E3A8A; color: #1E3A8A;">
                <h4>Pago Móvil Mercantil</h4>
                <p>V-15.214.337 | 04262272765 | Tasa BCV</p>
                <div style="background: #1E3A8A; color: #FFD700; padding: 10px; border-radius: 8px; text-align: center;">
                <h2>{total_bs:,.2f} Bs.</h2></div></div>""", unsafe_allow_html=True)

        with tab_co:
            st.markdown(f"""<div style="background-color: #FFF7ED; padding: 20px; border-radius: 12px; border: 1px solid #C2410C; color: #C2410C;">
                <h4>Transferencia Bancaria</h4>
                <p>Datos en proceso de actualización internacional.</p>
                <div style="background: #C2410C; color: white; padding: 10px; border-radius: 8px; text-align: center;">
                <h2>{total_cop:,.2f} COP</h2></div></div>""", unsafe_allow_html=True)

        with tab_usdt:
            st.markdown(f"""<div style="background-color: #F0FDF4; padding: 20px; border-radius: 12px; border: 1px solid #15803D; color: #15803D;">
                <h4>USDT (Red BEP20)</h4>
                <p style="word-break: break-all;">0xE30516Af847E0a7E343917e0C204E1e974754dBa</p>
                <div style="background: #15803D; color: white; padding: 10px; border-radius: 8px; text-align: center;">
                <h2>80.00 USDT</h2></div></div>""", unsafe_allow_html=True)

        ref = st.text_input("Número de Referencia de Transacción:")
        if st.button("🚀 FINALIZAR Y AGENDAR ESPECIALISTA", use_container_width=True):
            if ref:
                st.balloons()
                st.success("Expediente en firme. Un coordinador de agenda le contactará en 24 horas.")
            else:
                st.error("Por favor, ingrese la referencia para asignar su especialista.")
    else:
        st.warning("⚠️ **Protocolo de Seguridad:** Es imperativo completar primero el encuentro de decodificación con Nexo.")
        
