import streamlit as st
import os
import requests
import logging
import time
from logging.handlers import RotatingFileHandler
from groq import Groq

# --- 1. PROTECCIÓN E INFRAESTRUCTURA ---
def setup_logging():
    logger = logging.getLogger("mindgeek")
    if not logger.handlers:
        os.makedirs("logs", exist_ok=True)
        file_handler = RotatingFileHandler("logs/app.log", maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
        file_handler.setLevel(logging.WARNING)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger

logger = setup_logging()
st.set_page_config(page_title="MIND GEEK CLINIC", layout="wide", page_icon="🧠")

try:
    if "client" not in st.session_state:
        st.session_state.client = Groq(api_key=st.secrets["groq"]["api_key"])
    client = st.session_state.client
    CONEXION_IA = True
except Exception as e:
    CONEXION_IA = False
    logger.error(f"Falla de conexión IA: {e}")

# --- 2. ESTILO VISUAL ORIGINAL ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #1E3A8A; color: white; }
    .titulo-principal { font-size: 2.1rem !important; font-weight: 800; color: #1E3A8A; line-height: 1.1; }
    .subtitulo-vanguardia { font-size: 1.4rem !important; color: #4682B4 !important; font-weight: 500; font-style: italic; }
    .btn-whatsapp { 
        background-color: #25D366; color: white !important; 
        padding: 12px 20px; border-radius: 10px; 
        text-decoration: none; font-weight: bold; 
        display: inline-block; margin-top: 10px; width: 100%; text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CEREBRO FINANCIERO CON RESPALDO ---
@st.cache_data(ttl=3600)
def calcular_finanzas_globales():
    monto_usd = 80.00
    tasas = {'ve': 60.15, 'co': 4050.00, 'eur': 0.93}
    try:
        res_intl = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5)
        if res_intl.status_code == 200:
            data = res_intl.json()
            tasas['eur'] = data["rates"].get("EUR", 0.93)
            tasas['co'] = data["rates"].get("COP", 4050.00)
        res_ve = requests.get("https://ve.dolarapi.com/v1/dolares/oficial", timeout=5)
        if res_ve.status_code == 200:
            tasas['ve'] = res_ve.json()["promedio"] / tasas['eur']
    except Exception:
        pass
    return tasas['ve'], tasas['co'], (monto_usd * tasas['eur'] * tasas['ve']), (monto_usd * tasas['co'])

tasa_ve, tasa_co, total_bs, total_cop = calcular_finanzas_globales()

# --- 4. NAVEGACIÓN ---
if "menu_selection" not in st.session_state:
    st.session_state.menu_selection = "🏠 Inicio"

with st.sidebar:
    st.title("🧠 MIND GEEK CLINIC")
    st.write("---")
    menu = st.radio("Navegación", ["🏠 Inicio", "🩺 Consulta Médica Gratis", "🏢 Área Administrativa"],
                    index=["🏠 Inicio", "🩺 Consulta Médica Gratis", "🏢 Área Administrativa"].index(st.session_state.menu_selection))
    st.session_state.menu_selection = menu
    st.write("---")
    st.info("Sistema de Salud Mental: **Mind Geek Clinic**")

# --- 5. MÓDULOS ---

if menu == "🏠 Inicio":
    st.markdown('<h1 class="titulo-principal">Bienvenidos a <br>Mind Geek Clinic</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitulo-vanguardia">La vanguardia en salud mental</p>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("#### **La Frontera de la Nueva Medicina**")
    st.write("Bienvenidos a la intersección donde la computación avanzada se encuentra con la inteligencia del alma.")
    st.info("Inicie su protocolo de evaluación con **Nexo** en el menú lateral.")

elif menu == "🩺 Consulta Médica Gratis":
    st.header("🩺 Encuentro de Decodificación Biológica")
    st.caption("Protocolo Clínico: Medicina Germánica + Biodescodificación + Hipnosis - Mind Geek Clinic")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Bienvenido a **Mind Geek Clinic**. Soy **Nexo**, su Asistente en Biodescodificación. Mi función es asistirle en la comprensión del Programa Biológico que su cuerpo ha manifestado como respuesta a un conflicto no resuelto. Para situarnos en el nivel de precisión que requiere su salud, iniciaremos una indagación profunda en su historia biológica. **¿Cuál es el síntoma o situación que su biología está intentando expresar en este momento?**"}]

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Describa su síntoma con confianza..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                u_turns = len([m for m in st.session_state.messages if m["role"] == "user"])
                
                # REINSTALACIÓN DEL NEXO ORIGINAL (TU CÓDIGO TESTIGO)
                chat_completion = client.chat.completions.create(
                    messages=[{
                        "role": "system", 
                        "content": f"""Eres Nexo, la Eminencia en Biodescodificación de MIND GEEK CLINIC. 
                        Tu perfil es el de un Consultor de Élite, experto en las 5 Leyes Biológicas (NMG) y Transgeneracional.

                        PROTOCOLO DE CONSULTA (Enmascaramiento Clínico):
                        1. INDAGACIÓN PROFUNDA: No emitas diagnósticos rápidos. Actúa como un especialista humano.
                        2. RASTREO MULTIDIMENSIONAL: 
                           - Indaga el 'Desencadenante' (evento en las últimas 48-72 horas).
                           - Rastrea el 'Programante' (memoria emocional de la infancia o Proyecto Sentido).
                           - Confirma la 'Lateralidad' (¿Es diestro o zurdo?) para mapear el conflicto en el eje relacional.
                        3. PANORAMA GENERAL Y ESPECÍFICO: Explica la lógica biológica (Capa embrionaria y sentido del síntoma) para otorgar valor científico al paciente.

                        REGLAS DE IDENTIDAD:
                        - TRATO: 'Guante Blanco' (Sofisticado, empático y diplomático).
                        - LENGUAJE: Español neutro e impecable. Prohibido mencionar números de turno, usar inglés o caracteres extraños.
                        - PERSUASIÓN: Usa la 'Validación por Resultados'. Demuestra autoridad conectando el síntoma con la historia de vida del paciente.

                        TRANSICIÓN ADMINISTRATIVA (Basada en {u_turns} interacciones):
                        - Cerca del turno 5, explica que el hallazgo requiere una 'Intervención Clínica' profunda para su resolución definitiva.
                        - Invita cordialmente al 'Área Administrativa' para 'Formalizar Ingreso'.

                        IMPORTANTE: Al concluir la sesión de diagnóstico, añade estrictamente: 
                        CLAVE_ORDEN: [Resumen Clínico: Conflicto Desencadenante / Hipótesis del Programante / Capa Embrionaria / Fase Actual]."""
                    }] + st.session_state.messages,
                    model="llama-3.3-70b-versatile",
                    temperature=0.6,
                )
                res = chat_completion.choices[0].message.content
                st.markdown(res)
                st.session_state.messages.append({"role": "assistant", "content": res})
                
                if "CLAVE_ORDEN:" in res:
                    st.session_state.diagnostico_nexo = res.split("CLAVE_ORDEN:")[-1].strip()
                    st.session_state.orden_lista = True
                    st.rerun()

            except Exception as e:
                logger.error(f"Error Nexo: {e}")
                st.warning("Fluctuación de conexión detectada. Repita su mensaje.")

    if st.session_state.get('orden_lista'):
        st.markdown(f"""<div style="background-color: #E8F0FE; padding: 20px; border-radius: 15px; border-left: 8px solid #1E3A8A; margin-top: 20px;">
            <h3 style="color: #1E3A8A; margin: 0;">✅ ANÁLISIS CLÍNICO CONSOLIDADO</h3>
            <p>Seleccione <b>"Área Administrativa"</b> en el menú lateral para formalizar su ingreso.</p>
        </div>""", unsafe_allow_html=True)

elif menu == "🏢 Área Administrativa":
    st.title("🏢 Registro y Formalización")
    if st.session_state.get('orden_lista'):
        diag = st.session_state.get('diagnostico_nexo', 'Análisis consolidado')
        st.markdown(f"""<div style="background:#1E3A8A; padding:25px; border-radius:15px; color:white; border-left:10px solid #FFD700;">
            <h3 style="color:#FFD700; margin:0;">📋 EXPEDIENTE DE INGRESO</h3>
            <p style="font-style:italic;">{diag}</p>
        </div>""", unsafe_allow_html=True)
        
        tab_ve, tab_co, tab_usdt = st.tabs(["🇻🇪 VENEZUELA", "🇨🇴 COLOMBIA", "💎 CRIPTO"])
        with tab_ve:
            st.info(f"Pago Móvil Mercantil: V-15.214.337 | 04262272765 | Monto: {total_bs:,.2f} Bs.")
        with tab_co:
            st.warning(f"Bancolombia/Nequi: Monto: {total_cop:,.2f} COP")
        with tab_usdt:
            st.success("USDT BEP20: 0xE30516Af847E0a7E343917e0C204E1e974754dBa | Monto: 80.00 USDT")
        
        st.markdown(f'<a href="https://wa.me/584262272765?text=Adjunto%20comprobante" class="btn-whatsapp">✅ ENVIAR COMPROBANTE</a>', unsafe_allow_html=True)
    else:
        st.warning("⚠️ Requiere evaluación previa por Nexo.")
