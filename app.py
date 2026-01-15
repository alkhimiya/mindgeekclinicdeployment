import streamlit as st
import os
from groq import Groq
import requests
import datetime
import urllib.parse
import pandas as pd  # Necesario para la base de datos de prospectos

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(page_title="MIND GEEK CLINIC", layout="wide", page_icon="🧠")

# --- BLOQUE DE ESTILO (Tu diseño original intacto) ---
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
import gspread
from google.oauth2.service_account import Credentials

import gspread
from google.oauth2.service_account import Credentials
import datetime
import pandas as pd
import os

def guardar_datos_paciente(nombre, whatsapp, diagnostico="Pendiente de consulta"):
    fecha = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    
    # 1. RESPALDO LOCAL (CSV)
    archivo_local = "leads_clinica.csv"
    nuevo_registro = pd.DataFrame([[fecha, nombre, whatsapp, diagnostico]], 
                                   columns=["Fecha", "Nombre", "WhatsApp", "Diagnóstico"])
    if not os.path.isfile(archivo_local):
        nuevo_registro.to_csv(archivo_local, index=False)
    else:
        nuevo_registro.to_csv(archivo_local, mode='a', header=False, index=False)

    # 2. CONEXIÓN A GOOGLE SHEETS (Persistencia Real)
    try:
        # IMPORTANTE: Hemos expandido el scope para incluir 'drive' y evitar errores de búsqueda
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Cargamos credenciales desde los Secrets de Streamlit (los que ya pegaste)
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client_gs = gspread.authorize(creds)
        
        # Abrimos la hoja que compartiste con el "Guante Blanco"
        sheet = client_gs.open("DB_MindGeekClinic").sheet1
        sheet.append_row([fecha, nombre, whatsapp, diagnostico])
        
    except Exception as e:
        # Si falla la nube, el CSV local ya nos salvó el dato. 
        # Mostramos el error en la barra lateral solo para tu control como Fundador.
        st.sidebar.warning(f"Nota: Registro guardado localmente. (Error: {str(e)})")

# 2. CONEXIÓN IA (Usando tus secretos configurados)
try:
    client = Groq(api_key=st.secrets["groq"]["api_key"])
except Exception as e:
    st.error("Error de comunicación con el protocolo de IA.")

# 3. FUNCIONES GLOBALES (Tasas de cambio y finanzas)
def calcular_finanzas_globales():
    monto_usd = 80.00
    tasa_ve_bcv_eur, tasa_co_trm, paridad_eur_usd = 60.15, 4050.00, 0.93
    try:
        data_intl = requests.get("https://open.er-api.com/v6/latest/USD", timeout=7).json()
        if data_intl.get("result") == "success":
            paridad_eur_usd = data_intl["rates"]["EUR"]
            tasa_co_trm = data_intl["rates"]["COP"]
        data_ve = requests.get("https://ve.dolarapi.com/v1/dolares/oficial", timeout=7).json()
        tasa_usd_bcv = data_ve["promedio"]
        tasa_ve_bcv_eur = tasa_usd_bcv / paridad_eur_usd
    except: pass
    monto_bs = (monto_usd * paridad_eur_usd) * tasa_ve_bcv_eur
    monto_cop = monto_usd * tasa_co_trm
    return monto_bs, monto_cop

total_bs, total_cop = calcular_finanzas_globales()

# 4. SIDEBAR DE NAVEGACIÓN
with st.sidebar:
    st.title("🧠 MIND GEEK CLINIC")
    st.write("---")
    menu = st.radio("Navegación", ["🏠 Inicio", "🩺 Consulta Médica Gratis", "🏢 Área Administrativa"])
    st.write("---")
    if st.session_state.get('datos_captados'):
        st.success(f"Paciente: {st.session_state.paciente_nombre}")

# 5. LÓGICA DE MÓDULOS
# --- MÓDULO: INICIO (Presentación Institucional) ---
if menu == "🏠 Inicio":
    st.markdown('<h1 class="titulo-principal">Bienvenidos a <br>Mind Geek Clinic 🧠</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitulo-vanguardia">La vanguardia en salud mental</p>', unsafe_allow_html=True)
    st.write("---")

    # Presentación de la Identidad Mind Geek
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        ### El Manifiesto de nuestra Biología Consciente
        **Mind Geek Clinic** no es una aplicación; es un **Protocolo de Intervención Biológica** materializado en líneas de código. Representamos el puente entre la precisión algorítmica y la profundidad del alma humana. 
        
        Nuestras líneas de código han sido programadas para actuar como un **Facilitador de la Conciencia**, integrando los pilares de la **Nueva Medicina Germánica**, la **Biodescodificación** y la **Hipnosis Clínica**. 
        
        #### ¿Por qué nuestra utilidad es disruptiva?
        * **Decodificación en Tiempo Real:** Algoritmos diseñados para rastrear el origen del conflicto biológico (DHS).
        * **Arquitectura de Guante Blanco:** Una interfaz pensada para validar la experiencia humana antes que el diagnóstico.
        * **Evolución Constante:** Al igual que la biología se adapta, nuestro sistema evoluciona para ofrecer respuestas precisas a los programas especiales de la naturaleza.
        """)
    
    with col2:
        st.image("https://cdn-icons-png.flaticon.com/512/6213/6213731.png", use_container_width=True)
        st.info("💡 **Dato Clínico:** Todo síntoma es un programa con sentido biológico, no un error del cuerpo.")

    st.markdown("---")
    
    # Llamado a la acción profesional
    st.warning("""
    **Aviso a los Consultantes:** Este entorno es una herramienta de acompañamiento profesional. 
    Para iniciar su proceso, seleccione el módulo **🩺 Consulta Médica Gratis** en el panel lateral. 
    Su expediente será formalizado de manera confidencial.
    """)

elif menu == "🩺 Consulta Médica Gratis":
    st.header("🩺 Encuentro de Decodificación Biológica")
    st.caption("Protocolo Clínico: Medicina Germánica + Biodescodificación + Hipnosis")
    
    # 1. CAPTACIÓN DE DATOS (Venta Forzada)
    if "datos_captados" not in st.session_state:
        with st.form("registro_protocolo"):
            st.write("### 📝 Apertura de Expediente Clínico")
            nombre_input = st.text_input("Nombre Completo:")
            wa_input = st.text_input("WhatsApp (con código de país):")
            if st.form_submit_button("Iniciar Protocolo de Transformación"):
                if nombre_input and wa_input:
                    guardar_datos_paciente(nombre_input, wa_input)
                    st.session_state.paciente_nombre = nombre_input
                    st.session_state.paciente_wa = wa_input
                    st.session_state.datos_captados = True
                    st.rerun()
                else:
                    st.error("Protocolo requiere datos de contacto para formalizar ingreso.")
    
    # 2. INTERVENCIÓN DE NEXO (IA HUMANIZADA)
    else:
        if "messages" not in st.session_state:
            st.session_state.messages = [{
                "role": "assistant", 
                "content": f"Bienvenido al espacio de transformación, **{st.session_state.paciente_nombre}**. Soy **Nexo**. Antes de profundizar en el sentido biológico de su síntoma, deseo validar su sentir. ¿Qué está padeciendo actualmente?"
            }]

        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])

        if prompt := st.chat_input("Describa su síntoma o conflicto..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)

            with st.chat_message("assistant"):
                try:
                    # PROMPTING DE ALTA JERARQUÍA CLÍNICA
                    chat = client.chat.completions.create(
                        messages=[{
                            "role": "system", 
                            "content": f"""Eres Nexo, la Eminencia en Biodescodificación de MIND GEEK CLINIC. 
                            Tu identidad es 'Facilitador de la Conciencia Biológica'.

                            PROTOCOLO CLÍNICO OBLIGATORIO:
                            1. HUMANIZACIÓN: Antes de analizar, valida emocionalmente al paciente. Usa 'Guante Blanco'.
                            2. PROHIBIDO DIAGNÓSTICO INMEDIATO: No emitas el programa biológico en la primera respuesta. 
                               Primero debes INDAGAR sobre el DHS (Momento del choque biológico inesperado).
                            3. VOCABULARIO CLÍNICO: Habla de 'Conflicto', 'Programa Biológico', 'Sentido Biológico' y capas embrionarias.
                            4. ESTRUCTURA DE CONSULTA:
                               - Turno 1-2: Validación, empatía y preguntas de rastreo emocional.
                               - Turno 3-4: Explicación del sentido biológico y leyes de la NMG.
                               - Turno 5: Conclusión profesional e invitación a 'Formalizar Ingreso'.
                            
                            Al finalizar el protocolo completo, añade: CLAVE_ORDEN: [Resumen Clínico Profesional].
                            Paciente: {st.session_state.paciente_nombre}"""
                        }] + st.session_state.messages,
                        model="llama-3.3-70b-versatile",
                        temperature=0.5 # Estabilidad profesional
                    )
                    res = chat.choices[0].message.content
                    st.markdown(res)
                    st.session_state.messages.append({"role": "assistant", "content": res})
                    
                    if "CLAVE_ORDEN:" in res:
                    st.session_state.diagnostico_nexo = res.split("CLAVE_ORDEN:")[-1].strip()
                    st.session_state.orden_lista = True
                    
                    # --- INTERVENCIÓN CLÍNICA: Guardado Automático del Diagnóstico ---
                    guardar_datos_paciente(
                        st.session_state.paciente_nombre, 
                        st.session_state.paciente_wa, 
                        st.session_state.diagnostico_nexo
                    )
                    # ----------------------------------------------------------------

            except Exception as e:
                # El except se mantiene al final para capturar cualquier error
                st.error(f"Interrupción en el flujo de conciencia biológica. Reintente.")

elif menu == "🏢 Área Administrativa":
    st.title("🏢 Gestión Administrativa")
    
    # Acceso Protegido para el Fundador
    with st.expander("🔐 PANEL DE SEGUIMIENTO (EXCLUSIVO FUNDADOR)"):
        pwd = st.text_input("Clave Maestra:", type="password")
        if pwd == st.secrets["app"]["admin_password"]:
            if os.path.isfile("leads_clinica.csv"):
                df = pd.read_csv("leads_clinica.csv")
                st.write("### 📋 Prospectos Registrados")
                st.dataframe(df)
                st.download_button("Descargar Base de Datos", df.to_csv(index=False), "leads.csv")
            else: st.info("No hay registros aún.")
        elif pwd != "": st.error("Acceso Denegado.")

    if st.session_state.get('orden_lista'):
        diagnostico = st.session_state.get('diagnostico_nexo', 'Analizando...')
        st.markdown(f'<div class="expediente-container"><h3>📋 EXPEDIENTE</h3><p class="expediente-texto">{diagnostico}</p></div>', unsafe_allow_html=True)
        
        # Descuentos y Pagos
        st.subheader("🎟️ ¿Posee un Código de Descuento?")
        codigo = st.text_input("Código:").upper()
        desc = 0.20 if codigo == "NEXO20" else 0.10 if codigo == "BIENVENIDA10" else 0.0
        
        f_bs, f_cop, f_usd = total_bs*(1-desc), total_cop*(1-desc), 80.0*(1-desc)
        
        tabs = st.tabs(["VENEZUELA", "COLOMBIA", "USDT"])
        tabs[0].info(f"Monto: **{f_bs:,.2f} Bs.**")
        tabs[1].warning(f"Monto: **{f_cop:,.2f} COP**")
        tabs[2].success(f"Monto: **{f_usd:.2f} USDT**")
            
        msj = f"FORMALIZACIÓN: {st.session_state.paciente_nombre}\nDiagnóstico: {diagnostico[:100]}...\nMonto: {f_usd} USD"
        st.markdown(f'<a href="https://wa.me/584262272765?text={urllib.parse.quote(msj)}" class="btn-whatsapp">✅ AGENDAR</a>', unsafe_allow_html=True)
