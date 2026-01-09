import streamlit as st
import os
import requests
import logging
import time
from logging.handlers import RotatingFileHandler
from groq import Groq

# --- 1. INFRAESTRUCTURA DE SEGURIDAD Y LOGGING (Refinamiento 1) ---
def setup_logging():
    logger = logging.getLogger("mindgeek")
    if not logger.handlers:
        os.makedirs("logs", exist_ok=True)
        # Rota cada 5MB para no llenar el servidor
        file_handler = RotatingFileHandler(
            "logs/app.log", maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
        )
        file_handler.setLevel(logging.WARNING)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger

logger = setup_logging()

# Configuración de página
st.set_page_config(page_title="MIND GEEK CLINIC", layout="wide", page_icon="🧠")

# --- 2. GESTIÓN DE SALUD DE SESIÓN (Refinamiento 2) ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "menu_selection" not in st.session_state:
    st.session_state.menu_selection = "🏠 Inicio"

def manage_session_health():
    # Limpieza de historial para fluidez (Tarea 4)
    if len(st.session_state.messages) > 25:
        st.session_state.messages = st.session_state.messages[-15:]
    
    # Reset de diagnóstico tras 24h
    current_time = time.time()
    if st.session_state.get('orden_lista'):
        if 'diagnostico_time' not in st.session_state:
            st.session_state.diagnostico_time = current_time
        elif current_time - st.session_state.diagnostico_time > 86400:
            st.session_state.orden_lista = False
            st.session_state.diagnostico_nexo = None

manage_session_health()

# --- 3. CONEXIÓN IA (Capa Global Protegida - Tarea 1) ---
try:
    if "client" not in st.session_state:
        st.session_state.client = Groq(api_key=st.secrets["groq"]["api_key"])
    client = st.session_state.client
    CONEXION_IA = True
except Exception as e:
    CONEXION_IA = False
    logging.error(f"Falla crítica de enlace IA: {e}")

# --- 4. BLOQUE DE ESTILO CSS (Tu Identidad Visual) ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #1E3A8A; color: white; }
    .titulo-principal { font-size: 2.1rem !important; font-weight: 800; color: #1E3A8A; line-height: 1.1; }
    .subtitulo-vanguardia { font-size: 1.4rem !important; color: #4682B4 !important; font-weight: 500; font-style: italic; }
    .btn-whatsapp { 
        background-color: #25D366; color: white !important; 
        padding: 12px 20px; border-radius: 10px; 
        text-decoration: none; font-weight: bold; 
        display: inline-block; margin: 10px 0; width: 100%; text-align: center;
    }
    .expediente-box {
        background-color: #1E3A8A; padding: 25px; border-radius: 15px; 
        color: white; border-left: 10px solid #FFD700; box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 5. CEREBRO FINANCIERO (Tarea 3: Timeout y Respaldo) ---
@st.cache_data(ttl=3600) # Caché de 1 hora para no saturar APIs
def calcular_finanzas_globales():
    monto_usd = 80.00
    # Valores de RESPALDO (Protocolo de Seguridad)
    tasas = {'ve': 60.15, 'co': 4050.00, 'eur': 0.93}
    
    try:
        # A. Paridad e Internacional (Timeout corto)
        res_intl = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5)
        if res_intl.status_code == 200:
            data = res_intl.json()
            tasas['eur'] = data["rates"].get("EUR", 0.93)
            tasas['co'] = data["rates"].get("COP", 4050.00)

        # B. Tasa Venezuela (Timeout diferenciado)
        res_ve = requests.get("https://ve.dolarapi.com/v1/dolares/oficial", timeout=8)
        if res_ve.status_code == 200:
            tasas['ve'] = res_ve.json()["promedio"] / tasas['eur']
            
    except Exception as e:
        logging.warning(f"Usando tasas de respaldo: {e}")
    
    return tasas['ve'], tasas['co'], (monto_usd * tasas['eur'] * tasas['ve']), (monto_usd * tasas['co'])

tasa_ve, tasa_co, total_bs, total_cop = calcular_finanzas_globales()

# --- 6. NAVEGACIÓN ---
with st.sidebar:
    st.title("🧠 MIND GEEK CLINIC")
    st.write("---")
    menu = st.radio("Navegación", ["🏠 Inicio", "🩺 Consulta Médica Gratis", "🏢 Área Administrativa"], 
                    index=["🏠 Inicio", "🩺 Consulta Médica Gratis", "🏢 Área Administrativa"].index(st.session_state.menu_selection))
    st.session_state.menu_selection = menu
    st.write("---")
    if st.session_state.get('orden_lista'):
        st.success("✨ Expediente Nexo Activo")

# --- 7. LÓGICA DE MÓDULOS ---

# MÓDULO: INICIO
if menu == "🏠 Inicio":
    st.markdown('<h1 class="titulo-principal">Bienvenidos a <br>Mind Geek Clinic</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitulo-vanguardia">La vanguardia en salud mental</p>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("#### **La Frontera de la Nueva Medicina**")
    st.write("Bienvenidos a la intersección donde la computación avanzada se encuentra con la inteligencia del alma.")
    st.info("Inicie su protocolo de evaluación con **Nexo** en el menú lateral.")

# MÓDULO: CONSULTA MÉDICA
elif menu == "🩺 Consulta Médica Gratis":
    st.header("🩺 Encuentro de Decodificación Biológica")
    st.caption("Protocolo Clínico: Medicina Germánica + Biodescodificación + Hipnosis")
    
    if not st.session_state.messages:
        st.session_state.messages = [{"role": "assistant", "content": "Bienvenido a **Mind Geek Clinic**. Soy **Nexo**. ¿Cuál es el síntoma que su biología manifiesta?"}]

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    # Refinamiento 3: Feedback de éxito sin recargas bruscas
    if st.session_state.get('just_finished_diagnosis'):
        st.success("✅ Protocolo de Nexo finalizado. Su expediente ha sido derivado.")
        if st.button("Ir al Área Administrativa para formalizar ingreso ➡️"):
            st.session_state.menu_selection = "🏢 Área Administrativa"
            st.session_state.just_finished_diagnosis = False
            st.rerun()

    if prompt := st.chat_input("Describa su síntoma con confianza..."):
        if not CONEXION_IA:
            st.error("⚠️ El sistema Nexo está en mantenimiento preventivo. Intente en unos minutos.")
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)

            with st.chat_message("assistant"):
                try:
                    u_turns = len([m for m in st.session_state.messages if m["role"] == "user"])
                    chat_completion = client.chat.completions.create(
                        messages=[{"role": "system", "content": f"Eres Nexo, Eminencia en Biodescodificación. Protocolo: DHS, Lateralidad, Programante. Guante Blanco. Turnos: {u_turns}. CLAVE_ORDEN: [Resumen]."}] + st.session_state.messages,
                        model="llama-3.3-70b-versatile",
                        temperature=0.6,
                    )
                    res = chat_completion.choices[0].message.content
                    st.markdown(res)
                    st.session_state.messages.append({"role": "assistant", "content": res})
                    
                    if "CLAVE_ORDEN:" in res:
                        st.session_state.diagnostico_nexo = res.split("CLAVE_ORDEN:")[-1].strip()
                        st.session_state.orden_lista = True
                        st.session_state.just_finished_diagnosis = True
                        st.rerun()
                except Exception as e:
                    logging.error(f"Error en diálogo Nexo: {e}")
                    st.warning("Fluctuación de conexión detectada. Por favor, repita su mensaje.")

# MÓDULO: ÁREA ADMINISTRATIVA
elif menu == "🏢 Área Administrativa":
    st.title("🏢 Registro y Formalización de Ingreso")
    
    if st.session_state.get('orden_lista'):
        diag = st.session_state.get('diagnostico_nexo', 'Análisis consolidado')
        
        st.markdown(f"""
        <div class="expediente-box">
            <h3 style="color: #FFD700; margin:0;">📋 EXPEDIENTE DE INGRESO DIGITAL</h3>
            <p style="font-style: italic; margin-top:10px; color: #ECF0F1;">{diag}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("---")
        st.subheader("💳 Protocolos de Inversión")
        tab_ve, tab_co, tab_usdt = st.tabs(["🇻🇪 VENEZUELA", "🇨🇴 COLOMBIA", "💎 CRIPTO"])
        
        with tab_ve:
            st.markdown(f"""
                <div style="background-color: #1E3A8A; padding: 25px; border-radius: 15px; color: white;">
                    <h4 style="color: #FFD700;">🇻🇪 Pago Móvil Mercantil</h4>
                    <p><b>V-15.214.337</b> | <b>04262272765</b></p>
                    <p style="color: #BDC3C7;">Tasa BCV (Euro): {tasa_ve:,.2f} Bs.</p>
                    <h2 style="color: white; text-align: center;">{total_bs:,.2f} Bs.</h2>
                </div>
            """, unsafe_allow_html=True)

        with tab_co:
            st.markdown(f"""
                <div style="background-color: #D35400; padding: 25px; border-radius: 15px; color: white;">
                    <h4 style="color: #FFD700;">🇨🇴 Bancolombia / Nequi</h4>
                    <p><b>Referencia TRM:</b> {tasa_co:,.2f} COP</p>
                    <h2 style="color: white; text-align: center;">{total_cop:,.2f} COP</h2>
                </div>
            """, unsafe_allow_html=True)

        with tab_usdt:
            st.markdown(f"""
                <div style="background-color: #145A32; padding: 25px; border-radius: 15px; color: white;">
                    <h4 style="color: #FFD700;">💎 USDT (Red BEP20)</h4>
                    <code>0xE30516Af847E0a7E343917e0C204E1e974754dBa</code>
                    <h2 style="color: white; text-align: center;">80.00 USDT</h2>
                </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
            <a href="https://wa.me/584262272765?text=Adjunto%20mi%20comprobante" class="btn-whatsapp">
                ✅ ENVIAR COMPROBANTE POR WHATSAPP
            </a>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 FINALIZAR Y AGENDAR"):
            st.balloons()
            st.success("Registro administrativo completado.")
    else:
        st.warning("⚠️ Requiere evaluación previa por Nexo en la sección de Consulta Médica.")
