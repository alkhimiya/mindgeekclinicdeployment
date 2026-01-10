import streamlit as st
import os
from groq import Groq
import requests
import datetime
import urllib.parse

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(page_title="MIND GEEK CLINIC", layout="wide", page_icon="🧠")

# --- BLOQUE DE ESTILO (Copia fiel de tu versión blindada) ---
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
        background-color: #1E3A8A !important; 
        padding: 25px; 
        border-radius: 15px; 
        border-left: 10px solid #FFD700; 
        margin-bottom: 20px;
        color: white !important;
    }
    .expediente-texto {
        color: #FFFFFF !important;
        font-size: 1.15rem !important;
        line-height: 1.6;
    }
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
    st.info("Sistema de Salud Mental: **Mind Geek Clinic**")

# 4. FUNCIONES GLOBALES (Tus cálculos de alta precisión)
def calcular_finanzas_globales():
    monto_usd = 80.00
    tasa_ve_bcv_eur = 60.15  
    tasa_co_trm = 4050.00
    paridad_eur_usd = 0.93
    try:
        url_intl = "https://open.er-api.com/v6/latest/USD"
        res_intl = requests.get(url_intl, timeout=7)
        data_intl = res_intl.json()
        if data_intl.get("result") == "success":
            paridad_eur_usd = data_intl["rates"]["EUR"]
            tasa_co_trm = data_intl["rates"]["COP"]
        url_ve = "https://ve.dolarapi.com/v1/dolares/oficial" 
        res_ve = requests.get(url_ve, timeout=7)
        data_ve = res_ve.json()
        tasa_usd_bcv = data_ve["promedio"]
        tasa_ve_bcv_eur = tasa_usd_bcv / paridad_eur_usd
    except:
        pass
    monto_eur = monto_usd * paridad_eur_usd
    monto_bs = monto_eur * tasa_ve_bcv_eur
    monto_cop = monto_usd * tasa_co_trm
    return tasa_ve_bcv_eur, tasa_co_trm, monto_bs, monto_cop

tasa_ve, tasa_co, total_bs, total_cop = calcular_finanzas_globales()

# 5. LÓGICA DE MÓDULOS

# --- MÓDULO: INICIO (Copia Fiel con 🧠) ---
if menu == "🏠 Inicio":
    st.markdown('<h1 class="titulo-principal">Bienvenidos a <br>Mind Geek Clinic 🧠</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitulo-vanguardia">La vanguardia en salud mental</p>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("""
    #### **La Frontera de la Nueva Medicina**
    Bienvenidos a la intersección donde la computación avanzada se encuentra con la inteligencia del alma. 
    """)
    st.info("Inicie su protocolo de evaluación con **Nexo** en el menú lateral.")

# --- MÓDULO: CONSULTA MÉDICA (Nexo intacto) ---
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
                chat_completion = client.chat.completions.create(
                    messages=[{"role": "system", "content": f"""Eres Nexo, la Eminencia en Biodescodificación de MIND GEEK CLINIC. Tu perfil es el de un Consultor de Élite, experto en las 5 Leyes Biológicas (NMG) y Transgeneracional. PROTOCOLO DE CONSULTA: 1. INDAGACIÓN PROFUNDA. 2. RASTREO MULTIDIMENSIONAL. 3. PANORAMA GENERAL Y ESPECÍFICO. REGLAS DE IDENTIDAD: 'Guante Blanco', Español neutro, Validación por Resultados. TRANSICIÓN ADMINISTRATIVA: Cerca del turno 5 invita al 'Área Administrativa'. IMPORTANTE: Al concluir añade CLAVE_ORDEN: [Resumen Clínico]."""}] + st.session_state.messages,
                    model="llama-3.3-70b-versatile",
                    temperature=0.6,
                )
                res = chat_completion.choices[0].message.content
                st.markdown(res)
                st.session_state.messages.append({"role": "assistant", "content": res})
                if "CLAVE_ORDEN:" in res:
                    st.session_state.diagnostico_nexo = res.split("CLAVE_ORDEN:")[-1].strip()
                    st.session_state.orden_lista = True
            except:
                st.error("Error de comunicación biológica.")

# --- MÓDULO: ÁREA ADMINISTRATIVA (Tu base + Módulo de Citas) ---
elif menu == "🏢 Área Administrativa":
    st.title("🏢 Registro y Formalización")
    if st.session_state.get('orden_lista'):
        diagnostico = st.session_state.get('diagnostico_nexo', 'Analizando Programa Biológico...')
        st.markdown(f"""
            <div class="expediente-container">
                <h3 style="color: #FFD700; margin-top: 0;">📋 EXPEDIENTE DE DIAGNÓSTICO</h3>
                <p class="expediente-texto">{diagnostico}</p>
            </div>
        """, unsafe_allow_html=True)

        # NUEVO MÓDULO DE CITAS
        st.subheader("📅 Plan de Tratamiento (4 Sesiones)")
        st.write("Seleccione su fecha de inicio para proyectar el cronograma biológico.")
        hoy = datetime.date.today()
        fecha_1 = st.date_input("Sesión 1 (Inicio):", value=hoy + datetime.timedelta(days=2), min_value=hoy + datetime.timedelta(days=1))
        
        # Proyección de sesiones (Regla de 10 días promedio)
        f2, f3, f4 = [fecha_1 + datetime.timedelta(days=d) for d in [10, 20, 30]]
        col_c1, col_c2, col_c3, col_c4 = st.columns(4)
        col_c1.metric("Sesión 1", fecha_1.strftime('%d/%m'))
        col_c2.metric("Sesión 2", f2.strftime('%d/%m'))
        col_c3.metric("Sesión 3", f3.strftime('%d/%m'))
        col_c4.metric("Sesión 4", f4.strftime('%d/%m'))

        st.markdown("---")

        # Métodos de Pago Originales
        tab_ve, tab_co, tab_usdt = st.tabs(["🇻🇪 VENEZUELA", "🇨🇴 COLOMBIA", "💎 USDT"])
        with tab_ve: st.info(f"**Pago Móvil:** Mercantil | V-15.214.337 | 04262272765 | **{total_bs:,.2f} Bs.**")
        with tab_co: st.warning(f"**Bancolombia / Nequi:** Consultar | **{total_cop:,.2f} COP**")
        with tab_usdt: st.success(f"**USDT (BEP20):** 0xE30516Af847E0a7E343917e0C204E1e974754dBa | **80.00 USDT**")
            
        # WhatsApp Inteligente
        mensaje_wa = f"Hola Fundador, completé mi diagnóstico.\n\n📍 *Diagnóstico:* {diagnostico[:100]}...\n📅 *Inicio:* {fecha_1.strftime('%d/%m/%Y')}\n💳 *Monto:* 80 USD"
        wa_link = f"https://wa.me/584262272765?text={urllib.parse.quote(mensaje_wa)}"
        st.markdown(f'<a href="{wa_link}" class="btn-whatsapp">✅ AGENDAR Y ENVIAR COMPROBANTE</a>', unsafe_allow_html=True)
    else:
        st.warning("⚠️ Protocolo no concluido. Regrese a la consulta con Nexo.")
