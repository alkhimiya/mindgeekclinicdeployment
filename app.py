import streamlit as st
import os
from groq import Groq
import requests
import datetime
import urllib.parse
import pandas as pd # Necesario para la base de datos de leads

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(page_title="MIND GEEK CLINIC", layout="wide", page_icon="🧠")

# --- BLOQUE DE ESTILO (Original) ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #1E3A8A; color: white; }
    .stChatFloatingInputContainer { bottom: 20px; }
    .titulo-principal { font-size: 2.1rem !important; font-weight: 800; color: #1E3A8A; line-height: 1.1; }
    .subtitulo-vanguardia { font-size: 1.4rem !important; color: #4682B4 !important; font-weight: 500; font-style: italic; }
    .btn-whatsapp { 
        background-color: #25D366; color: white !important; 
        padding: 12px 20px; border-radius: 10px; 
        text-decoration: none; font-weight: bold; 
        display: inline-block; margin-top: 10px;
        width: 100%; text-align: center;
    }
    .expediente-container {
        background-color: #1E3A8A !important; padding: 25px; border-radius: 15px; 
        border-left: 10px solid #FFD700; margin-bottom: 20px; color: white !important;
    }
    .expediente-texto { color: #FFFFFF !important; font-size: 1.15rem !important; line-height: 1.6; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIÓN DE RESPALDO DE LEADS (Venta Forzada) ---
def guardar_datos_paciente(nombre, whatsapp):
    archivo = "leads_clinica.csv"
    nuevo_registro = pd.DataFrame([[datetime.datetime.now().strftime("%d/%m/%Y %H:%M"), nombre, whatsapp]], 
                                   columns=["Fecha", "Nombre", "WhatsApp"])
    if not os.path.isfile(archivo):
        nuevo_registro.to_csv(archivo, index=False)
    else:
        nuevo_registro.to_csv(archivo, mode='a', header=False, index=False)

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
    st.info("Sistema de Salud Mental: **Mind Geek Clinic**")

# 4. FUNCIONES GLOBALES (Tasas de cambio)
def calcular_finanzas_globales():
    monto_usd = 80.00
    tasa_ve_bcv_eur, tasa_co_trm, paridad_eur_usd = 60.15, 4050.00, 0.93
    try:
        res_intl = requests.get("https://open.er-api.com/v6/latest/USD", timeout=7).json()
        if res_intl.get("result") == "success":
            paridad_eur_usd = res_intl["rates"]["EUR"]
            tasa_co_trm = res_intl["rates"]["COP"]
        data_ve = requests.get("https://ve.dolarapi.com/v1/dolares/oficial", timeout=7).json()
        tasa_ve_bcv_eur = data_ve["promedio"] / paridad_eur_usd
    except: pass
    return tasa_ve_bcv_eur, tasa_co_trm, (monto_usd * paridad_eur_usd) * tasa_ve_bcv_eur, monto_usd * tasa_co_trm

tasa_ve, tasa_co, total_bs, total_cop = calcular_finanzas_globales()

# 5. MÓDULOS

if menu == "🏠 Inicio":
    st.markdown('<h1 class="titulo-principal">Bienvenidos a <br>Mind Geek Clinic 🧠</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitulo-vanguardia">La vanguardia en salud mental</p>', unsafe_allow_html=True)
    st.info("Inicie su protocolo en el menú lateral.")

elif menu == "🩺 Consulta Médica Gratis":
    st.header("🩺 Encuentro de Decodificación Biológica")
    
    if "datos_captados" not in st.session_state:
        with st.form("registro_protocolo"):
            st.write("### 📝 Apertura de Expediente")
            nombre_input = st.text_input("Nombre Completo:")
            wa_input = st.text_input("WhatsApp (con código de país):")
            if st.form_submit_button("Iniciar Protocolo Biológico"):
                if nombre_input and wa_input:
                    guardar_datos_paciente(nombre_input, wa_input) # CAPTURA PARA VENTA
                    st.session_state.paciente_nombre, st.session_state.paciente_wa = nombre_input, wa_input
                    st.session_state.datos_captados = True
                    st.rerun()
                else: st.error("Complete sus datos.")
    
    if st.session_state.get('datos_captados'):
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": f"Bienvenido **{st.session_state.paciente_nombre}**. Soy **Nexo**. ¿Cuál es el síntoma que su biología expresa?"}]
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])
        if prompt := st.chat_input("Describa su síntoma..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"):
                try:
                    chat = client.chat.completions.create(
                        messages=[{"role": "system", "content": "Eres Nexo, Eminencia en Biodescodificación. Usa Guante Blanco. Al concluir añade CLAVE_ORDEN: [Resumen]."}] + st.session_state.messages,
                        model="llama-3.3-70b-versatile",
                        temperature=0.6,
                    )
                    res = chat.choices[0].message.content
                    st.markdown(res)
                    st.session_state.messages.append({"role": "assistant", "content": res})
                    if "CLAVE_ORDEN:" in res:
                        st.session_state.diagnostico_nexo = res.split("CLAVE_ORDEN:")[-1].strip()
                        st.session_state.orden_lista = True
                except: st.error("Error biológico.")

elif menu == "🏢 Área Administrativa":
    st.title("🏢 Gestión Administrativa")
    
    # PANEL BLINDADO CON TUS SECRETOS
    with st.expander("🔐 PANEL DE SEGUIMIENTO (EXCLUSIVO FUNDADOR)"):
        pass_check = st.text_input("Clave Maestra:", type="password")
        if pass_check == st.secrets["app"]["admin_password"]: # Usa "Enaraure25.." de tus Secrets
            if os.path.isfile("leads_clinica.csv"):
                df = pd.read_csv("leads_clinica.csv")
                st.write("### 📋 Prospectos Registrados")
                st.dataframe(df)
                st.download_button("Descargar Base de Datos", df.to_csv(index=False), "leads.csv")
            else: st.info("No hay registros.")
        elif pass_check != "": st.error("Código incorrecto.")

    if st.session_state.get('orden_lista'):
        diagnostico = st.session_state.get('diagnostico_nexo', 'Analizando...')
        st.markdown(f'<div class="expediente-container"><h3>📋 EXPEDIENTE</h3><p class="expediente-texto">{diagnostico}</p></div>', unsafe_allow_html=True)
        
        st.subheader("🎟️ ¿Posee un Código de Descuento?")
        codigo_input = st.text_input("Ingrese código:").upper()
        desc = 0.20 if codigo_input == "NEXO20" else 0.10 if codigo_input == "BIENVENIDA10" else 0.0
        
        f_bs, f_cop, f_usd = total_bs*(1-desc), total_cop*(1-desc), 80.0*(1-desc)
        tabs = st.tabs(["🇻🇪 VENEZUELA", "🇨🇴 COLOMBIA", "💎 USDT"])
        tabs[0].info(f"Monto: **{f_bs:,.2f} Bs.**")
        tabs[1].warning(f"Monto: **{f_cop:,.2f} COP**")
        tabs[2].success(f"Monto: **{f_usd:.2f} USDT**")
            
        msj_wa = f"FORMALIZACIÓN: {st.session_state.paciente_nombre}\nMonto: {f_usd} USD"
        st.markdown(f'<a href="https://wa.me/584262272765?text={urllib.parse.quote(msj_wa)}" class="btn-whatsapp">✅ AGENDAR</a>', unsafe_allow_html=True)
    else: st.warning("⚠️ Protocolo incompleto.")
