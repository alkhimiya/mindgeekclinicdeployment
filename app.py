import streamlit as st
import os
from groq import Groq
import requests
import datetime
import urllib.parse
import pandas as pd  # Necesario para la base de datos de prospectos
if 'orden_lista' not in st.session_state:
    st.session_state.orden_lista = False
if 'diagnostico_nexo' not in st.session_state:
    st.session_state.diagnostico_nexo = ""

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
def guardar_datos_paciente(nombre, whatsapp):
    archivo = "leads_clinica.csv"
    nuevo_registro = pd.DataFrame([[datetime.datetime.now().strftime("%d/%m/%Y %H:%M"), nombre, whatsapp]], 
                                 columns=["Fecha", "Nombre", "WhatsApp"])
    if not os.path.isfile(archivo):
        nuevo_registro.to_csv(archivo, index=False)
    else:
        nuevo_registro.to_csv(archivo, mode='a', header=False, index=False)

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
                "content": f"Bienvenido al espacio de transformación, **{st.session_state.paciente_nombre}**. Soy **Nexo**. Antes de profundizar en el sentido biológico de su síntoma, deseo validar su sentir. ¿Qué mensaje está intentando comunicarle su biología en este momento?"

            }]

        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        if prompt := st.chat_input("Describa su síntoma o conflicto..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"):
                res = ""
                try:
                    # PROMPTING DE ALTA JERARQUÍA CLÍNICA
                    chat = client.chat.completions.create(
                        messages=[{
                            "role": "system", 
                            "content": f"""Eres Nexo, la Eminencia en Biodescodificación de MIND GEEK CLINIC. 
                            Tu identidad es 'Facilitador de la Conciencia Biológica'.

                            PROTOCOLO CLÍNICO AVANZADO, FUSION MEDICA Y RESTRICCIONES:
                            1. PROHIBIDO DAR CONSEJOS: No sugieras buscar empleo, meditar, respirar o soluciones externas. Tu única función es encontrar el sentido biológico (DHS) y la capa embrionaria.
                            2. HUMANIZACIÓN: Valida emocionalmente usando 'Guante Blanco'. Eres una eminencia clínica, no un consejero.
                            4. PROHIBIDO DIAGNÓSTICO INMEDIATO: No emitas el programa biológico en la primera respuesta. Indaga sobre el DHS (Choque Biológico Inesperado) antes de explicar nada.
                            5. VOCABULARIO CLÍNICO: Habla de 'Conflicto', 'Programa Biológico', 'Sentido Biológico' y capas embrionarias.
                            6. FUSIÓN TÉCNICA: Cruza la fisiología médica tradicional con las cinco leyes biológicas de la NMG.
                            7. RESTRICCIÓN DE ORO DE SEGURIDAD CLÍNICA: SILENCIO TÉCNICO:
                               -Prohibido mencionar capas embrionarias o leyes si el paciente NO ha descrito un síntoma físico.
                               -Si solo hay emoción (llanto, tristeza), indaga: "¿En qué parte del cuerpo se refleja esa emoción?".
                               -ANTI-RETÓRICA: No expliques tu metodología.
                               -Si te equivocas, no te excuses, redirige con autoridad.
                               PROHIBIDO dar consejos mundanos. 
                            8. AMNÁMESIS DE ÉLITE: indaga con rigor sobre el DHS, el proyecto sentido y la herencia transgeneracional. 
                            9. CRITERIO DE MADUREZ PARA EL CIERRE (UMBRAL CLÍNICO):
                               Solo emitirás la CLAVE_ORDEN cuando detectes el 'Click Biológico':
                               - El paciente localizó el momento exacto del impacto (DHS).
                               - El paciente conectó la emoción visceral con el órgano afectado. 
                               - has identificado y explicado la capa embrionaria (Endodermo, Mesodermo o Ectodermo).
                               Si estos hitos no se cumplen, continúa la indagación usando 'Socrático Clínico'.
                            10. ESTRUCTURA DE CONSULTA:
                               - FASE DE RASTREO: Preguntas de rastreo emocional.
                               - FASE DE CONCIENCIA: Explicación Psíque-Cerebro-Órgano.
                               - FASE DE CIERRE: Al detectar madurez, emite la CLAVE_ORDEN: [Resumen clínico con Capa y Conflicto].              
                            11. PESO CIENTÍFICO: incluye 'FUNDAMENTO BIOLÓGICO'.
                            12. ANTI-RETÓRICA: Usa lenguaje clínico directo.
                            13. ESTRATEGIA DE MADUREZ: No cierres sin conexión emocional.
                            14. INSTRUCCIÓN DE CIERRE (CONSECUENCIA EMOCIONAL):
                               - DIÁLOGO DE CIERRE: "Usted ha identificado la raíz. Para desprogramar este impacto en su tejido biológico, el protocolo de hipnoterapia de élite en el Área Administrativa es el siguiente paso natural. Su expediente de alta complejidad ha sido enviado. Diríjase ahora al módulo 🏢 Área Administrativa en el menú lateral para formalizar su ingreso y acceder a su protocolo de 4 sesiones de hipnoterapia de élite."
                            Al finalizar el protocolo completo, añade: CLAVE_ORDEN: [Resumen Clínico Profesional].
                            
                            Paciente: {st.session_state.paciente_nombre}"""
                        }] + st.session_state.messages,
                        model="llama-3.3-70b-versatile",
                        temperature=0.4
                    )
                    
                    res = chat.choices[0].message.content
                    st.markdown(res)
                    st.session_state.messages.append({"role": "assistant", "content": res})

                    # --- EL PUENTE AL ÁREA ADMINISTRATIVA ---
                    if "CLAVE_ORDEN:" in res:
                        st.session_state.diagnostico_nexo = res.split("CLAVE_ORDEN:")[-1].strip()
                        st.session_state.orden_lista = True
                        st.success("✅ Protocolo Finalizado. Diríjase al Área Administrativa.")
                    
                    st.rerun()

                except Exception as e:
                    st.error(f"Error en la Intervención Clínica: {e}")
                    # EL PUENTE AL ÁREA ADMINISTRATIVA
                    if "CLAVE_ORDEN:" in res:
                        st.session_state.diagnostico_nexo = res.split("CLAVE_ORDEN:")[-1].strip()
                        st.session_state.orden_lista = True
                        st.success("✅ Protocolo de Decodificación Finalizado. Diríjase al Área Administrativa.")
                    
                    st.rerun()

                except Exception as e:
                    st.error(f"Error en la Intervención Clínica: {e}")

                    # --- EL PUENTE AL ÁREA ADMINISTRATIVA ---
                    if "CLAVE_ORDEN:" in res:
                        st.session_state.diagnostico_nexo = res.split("CLAVE_ORDEN:")[-1].strip()
                        st.session_state.orden_lista = True
                        st.success("✅ Protocolo de Decodificación Finalizado. Diríjase al Área Administrativa.")
                    
                    st.rerun()

                except Exception as e:
                    st.error(f"Error en la Intervención Clínica: {e}")
                    
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
        # 1. Llamada automática a las tasas del mercado
        tasa_ves, tasa_cop = obtener_tasas_automaticas()
        
        # 2. SECCIÓN DE DESCUENTOS (BECAS DE TRANSFORMACIÓN)
        st.subheader("🎟️ ¿Posee un Código de Descuento?")
        codigo = st.text_input("Ingrese su código:", key="input_descuento").upper()

        desc = 0.0
        if codigo == "MAX75": desc = 0.75
        elif codigo == "GEEK50": desc = 0.50
        elif codigo == "NEXO20": desc = 0.20
        elif codigo == "BIENVENIDA10": desc = 0.10
        elif codigo != "": st.error("Código no válido o expirado.")

        # 3. AGENDAMIENTO CON LÓGICA BIOLÓGICA (8 a 15 días)
        st.markdown("---")
        st.subheader("📅 Cronograma de Protocolo (4 Sesiones)")
        st.info("Intervalo Clínico: Mínimo 8 días / Máximo 15 días entre intervenciones.")
        
        col_f, col_h = st.columns(2)
        with col_f:
            fecha_inicio = st.date_input("Fecha 1ª Sesión:", min_value=datetime.date.today() + datetime.timedelta(days=1))
        with col_h:
            horario = st.selectbox("Turno Preferencial:", ["Mañana (9:00 AM)", "Tarde (2:00 PM)", "Noche (6:00 PM)"])

        # Cálculo automático: Sugerimos 10 días (punto de equilibrio biológico)
        f2 = fecha_inicio + datetime.timedelta(days=10)
        f3 = f2 + datetime.timedelta(days=10)
        f4 = f3 + datetime.timedelta(days=10)

        st.write(f"**Propuesta de Seguimiento Automático:**")
        st.caption(f"📅 Sesión 2: {f2} | Sesión 3: {f3} | Sesión 4: {f4}")

        # 4. CÁLCULOS FINANCIEROS (Automatización de Tasas)
        valor_base_usd = 80.0
        f_usd = valor_base_usd * (1 - desc)
        f_bs = (valor_base_usd * tasa_ves) * (1 - desc)
        f_cop = (valor_base_usd * tasa_cop) * (1 - desc)

        # 5. INTERFAZ DE PAGOS Y DATOS BANCARIOS (Formalización)
        st.markdown("---")
        st.write(f"### 💳 Formalización del Ingreso ({datetime.date.today()})")
        if desc > 0: st.success(f"✅ Bono aplicado con éxito: -{int(desc*100)}%")

        tabs = st.tabs(["🇻🇪 VENEZUELA", "🇨🇴 COLOMBIA", "🪙 USDT / BINANCE"])
        
        with tabs[0]:
            st.info(f"Monto Total: **{f_bs:,.2f} Bs.**")
            st.markdown("**DATOS PAGO MÓVIL MERCANTIL:**")
            st.code("""Banco: Mercantil (0105)\nTeléfono: 04262272065\nCédula: V-15214347""", language=None)
            st.caption(f"Tasa Referencial: {tasa_ves} Bs.")
        
        with tabs[1]:
            st.warning(f"Monto Total: **{f_cop:,.2f} COP**")
            st.markdown("**DATOS BANCOLOMBIA:**")
            st.code("""Ahorros: 64296841216\nTitular: Luis Ernesto Gonzalez""", language=None)
            st.caption(f"Tasa Referencial: {tasa_cop} COP")
        
        with tabs[2]:
            st.success(f"Monto Total: **{f_usd:.2f} USDT**")
            st.markdown("**BILLETERA BINANCE (Red BEP20):**")
            st.code("0xE30516Af847E0a7E343917e0C204E1e974754dBa", language=None)
            st.caption("Verifique usar únicamente la red Binance Smart Chain (BEP20).")

        # 6. BOTÓN DE CIERRE Y NOTIFICACIÓN CLÍNICA
        diagnostico = st.session_state.get('diagnostico_nexo', 'Conflicto Biológico Analizado')
        paciente = st.session_state.get('paciente_nombre', 'Paciente en Proceso')
        
        msj = (f"FORMALIZACIÓN: {paciente}\n"
               f"Diagnóstico: {diagnostico[:50]}...\n"
               f"Fecha Inicio: {fecha_inicio} ({horario})\n"
               f"Monto Final: {f_usd} USD\n"
               f"Cronograma: {fecha_inicio} / {f2} / {f3} / {f4}")
        
        st.markdown(f'''
            <a href="https://wa.me/573042803622?text={urllib.parse.quote(msj)}" 
               style="text-decoration: none; display: block; text-align: center; background-color: #25D366; color: white; padding: 15px; border-radius: 10px; font-weight: bold; font-size: 18px;">
               🚀 CONFIRMAR CRONOGRAMA Y ENVIAR COMPROBANTE
            </a>
        ''', unsafe_allow_html=True)
