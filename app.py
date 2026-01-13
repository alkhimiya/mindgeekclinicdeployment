import os
from groq import Groq
import requests
import datetime
import urllib.parse

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(page_title="MIND GEEK CLINIC", layout="wide", page_icon="🧠")

# --- BLOQUE DE ESTILO (Tu código satisfactorio intacto) ---
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

# 4. FUNCIONES GLOBALES
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
    except Exception as e:
        pass
    monto_eur = monto_usd * paridad_eur_usd
    monto_bs = monto_eur * tasa_ve_bcv_eur
    monto_cop = monto_usd * tasa_co_trm
    return tasa_ve_bcv_eur, tasa_co_trm, monto_bs, monto_cop

tasa_ve, tasa_co, total_bs, total_cop = calcular_finanzas_globales()

# 5. LÓGICA DE MÓDULOS

# --- MÓDULO: INICIO ---
if menu == "🏠 Inicio":
    st.markdown('<h1 class="titulo-principal">Bienvenidos a <br>Mind Geek Clinic 🧠</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitulo-vanguardia">La vanguardia en salud mental</p>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("""
    #### **La Frontera de la Nueva Medicina**
    Bienvenidos a la intersección donde la computación avanzada se encuentra con la inteligencia del alma. 
    """)
    st.info("Inicie su protocolo de evaluación con **Nexo** en el menú lateral.")

# --- MÓDULO: CONSULTA MÉDICA (Con Inserción de Captación) ---
elif menu == "🩺 Consulta Médica Gratis":
    st.header("🩺 Encuentro de Decodificación Biológica")
    st.caption("Protocolo Clínico: Medicina Germánica + Biodescodificación + Hipnosis - Mind Geek Clinic")
    
    # INSERCIÓN: Captación para Venta Forzada
    if "datos_captados" not in st.session_state:
        with st.form("registro_protocolo"):
            st.write("### 📝 Apertura de Expediente")
            nombre_input = st.text_input("Nombre Completo:")
            wa_input = st.text_input("WhatsApp (con código de país):")
            if st.form_submit_button("Iniciar Protocolo Biológico"):
                if nombre_input and wa_input:
                    st.session_state.paciente_nombre = nombre_input
                    st.session_state.paciente_wa = wa_input
                    st.session_state.datos_captados = True
                    st.rerun()
                else:
                    st.error("Datos necesarios para el seguimiento clínico.")
    
    # Solo muestra Nexo si ya se registró
    if st.session_state.get('datos_captados'):
        if "messages" not in st.session_state:
            st.session_state.messages = [{
                "role": "assistant", 
                "content": f"Bienvenido **{st.session_state.paciente_nombre}**. Soy **Nexo**, su Asistente en Biodescodificación. ¿Cuál es el síntoma que su biología está intentando expresar?"
            }]

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Describa su síntoma con confianza..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)

            with st.chat_message("assistant"):
                try:
                    u_turns = len([m for m in st.session_state.messages if m["role"] == "user"])
                    chat_completion = client.chat.completions.create(
                        messages=[{
                            "role": "system", 
                            "content": f"""Eres Nexo, la Eminencia en Biodescodificación de MIND GEEK CLINIC. 
                            PROTOCOLO DE CONSULTA: INDAGACIÓN, RASTREO Y PANORAMA.
                            REGLAS: 'Guante Blanco', Validación por Resultados. 
                            TRANSICIÓN ADMINISTRATIVA: Cerca del turno 5, invita a 'Formalizar Ingreso'.
                            IMPORTANTE: Al concluir, añade CLAVE_ORDEN: [Resumen Clínico]."""
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
                except Exception as e:
                    st.error("Error de comunicación biológica.")

# --- MÓDULO: ÁREA ADMINISTRATIVA (Con Inserción de Descuento) ---
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
        
        # INSERCIÓN: Descuento
        st.subheader("🎟️ ¿Posee un Código de Descuento?")
        codigo_input = st.text_input("Ingrese código:").upper()
        porcentaje_desc = 0.20 if codigo_input == "NEXO20" else 0.10 if codigo_input == "BIENVENIDA10" else 0.0
        if porcentaje_desc > 0: st.success(f"Descuento de {int(porcentaje_desc*100)}% aplicado.")

        # Recálculo de montos con descuento
        final_bs = total_bs * (1 - porcentaje_desc)
        final_cop = total_cop * (1 - porcentaje_desc)
        final_usd = 80.00 * (1 - porcentaje_desc)

        st.subheader("📅 Plan de Tratamiento (4 Sesiones)")
        hoy = datetime.date.today()
        fecha_1 = st.date_input("Sesión 1 (Inicio):", value=hoy + datetime.timedelta(days=2), min_value=hoy + datetime.timedelta(days=1))
        f2, f3, f4 = [fecha_1 + datetime.timedelta(days=d) for d in [10, 20, 30]]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Inicio", fecha_1.strftime('%d/%m'))
        c2.metric("S2", f2.strftime('%d/%m'))
        c3.metric("S3", f3.strftime('%d/%m'))
        c4.metric("S4", f4.strftime('%d/%m'))

        tab_ve, tab_co, tab_usdt = st.tabs(["🇻🇪 VENEZUELA", "🇨🇴 COLOMBIA", "💎 USDT"])
        with tab_ve:
            st.info(f"**Pago Móvil:** Mercantil | V-15.214.337 | 04262272765 | Monto: **{final_bs:,.2f} Bs.**")
        with tab_co:
            st.warning(f"**Bancolombia / Nequi:** Monto: **{final_cop:,.2f} COP**")
        with tab_usdt:
            st.success(f"**USDT (BEP20):** 0xE30516Af847E0a7E343917e0C204E1e974754dBa | **{final_usd:.2f} USDT**")
            
        # WHATSAPP: Mensaje con datos captados para tu venta directa
        numero_destino = "584262272765"
        msj_wa = (
            f"FORMALIZACIÓN DE INGRESO\n"
            f"Paciente: {st.session_state.paciente_nombre}\n"
            f"WhatsApp: {st.session_state.paciente_wa}\n"
            f"Inicio: {fecha_1}\n"
            f"Monto: {final_usd} USD\n"
            f"Diagnóstico: {diagnostico[:100]}..."
        )
        wa_link = f"https://wa.me/{numero_destino}?text={urllib.parse.quote(msj_wa)}"
        
        st.markdown(f'<a href="{wa_link}" class="btn-whatsapp">✅ AGENDAR Y ENVIAR COMPROBANTE</a>', unsafe_allow_html=True)
    else:
        st.warning("⚠️ Su protocolo aún no ha concluido. Regrese a la consulta con Nexo.")
