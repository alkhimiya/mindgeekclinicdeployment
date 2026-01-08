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
    .btn-whatsapp { 
        background-color: #25D366; color: white !important; 
        padding: 12px 20px; border-radius: 10px; 
        text-decoration: none; font-weight: bold; 
        display: inline-block; margin-top: 10px;
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

# 4. FUNCIONES GLOBALES (Cerebro Financiero de Alta Precisión y Automatización)
import requests

# Eliminamos el cache para forzar la actualización en vivo durante la verificación
def calcular_finanzas_globales():
    monto_usd = 80.00
    
    # Valores de RESPALDO (Solo si falla la conexión)
    # AJUSTE ESTOS VALORES A LO QUE VE EN EL BCV AHORA MISMO
    tasa_ve_bcv_eur = 60.15  
    tasa_co_trm = 4050.00
    paridad_eur_usd = 0.93

    try:
        # A. PARIDAD INTERNACIONAL
        url_intl = "https://open.er-api.com/v6/latest/USD"
        res_intl = requests.get(url_intl, timeout=7)
        data_intl = res_intl.json()
        
        if data_intl.get("result") == "success":
            paridad_eur_usd = data_intl["rates"]["EUR"]
            tasa_co_trm = data_intl["rates"]["COP"]

        # B. TASA OFICIAL VENEZUELA (Portal BCV)
        # Usamos una API alternativa más estable que apunta directo al BCV
        url_ve = "https://ve.dolarapi.com/v1/dolares/oficial" 
        res_ve = requests.get(url_ve, timeout=7)
        data_ve = res_ve.json()
        
        # El BCV publica el USD oficial, calculamos el EURO BCV con paridad
        tasa_usd_bcv = data_ve["promedio"]
        # La relación legal es Tasa USD * (1/Paridad) para obtener el Euro BCV
        tasa_ve_bcv_eur = tasa_usd_bcv / paridad_eur_usd
        
    except Exception as e:
        # Si desea ver el error técnico, descomente la siguiente línea:
        # st.error(f"Error de conexión financiera: {e}")
        pass

    # --- PROTOCOLO DE CONVERSIÓN ---
    monto_eur = monto_usd * paridad_eur_usd
    monto_bs = monto_eur * tasa_ve_bcv_eur
    monto_cop = monto_usd * tasa_co_trm
    
    return tasa_ve_bcv_eur, tasa_co_trm, monto_bs, monto_cop

# Inyección de datos
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
    """)
    st.info("Inicie su protocolo de evaluación con **Nexo** en el menú lateral.")

# --- MÓDULO: CONSULTA MÉDICA (Protocolo Nexo de Élite con Puente de Navegación) ---
elif menu == "🩺 Consulta Médica Gratis":
    st.header("🩺 Encuentro de Decodificación Biológica")
    st.caption("Protocolo Clínico: Medicina Germánica + Biodescodificación + Hipnosis - Mind Geek Clinic")
    
    # 1. BIENVENIDA CON PERSONALIDAD REFINADA
    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant", 
            "content": "Bienvenido a **Mind Geek Clinic**. Soy **Nexo**, su Asistente en Biodescodificación. Mi función es asistirle en la comprensión del Programa Biológico que su cuerpo ha manifestado como respuesta a un conflicto no resuelto. Para situarnos en el nivel de precisión que requiere su salud, iniciaremos una indagación profunda en su historia biológica. **¿Cuál es el síntoma o situación que su biología está intentando expresar en este momento?**"
        }]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Describa su síntoma con confianza..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                # Conteo silencioso para el enmascaramiento clínico
                u_turns = len([m for m in st.session_state.messages if m["role"] == "user"])
                
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
                
                # CAPTURA TÉCNICA PARA EL EXPEDIENTE ADMINISTRATIVO
                if "CLAVE_ORDEN:" in res:
                    st.session_state.diagnostico_nexo = res.split("CLAVE_ORDEN:")[-1].strip()
                    st.session_state.orden_lista = True
                elif "Área Administrativa" in res and u_turns >= 5:
                    st.session_state.diagnostico_nexo = "Análisis Clínico en Proceso de Transferencia Especializada"
                    st.session_state.orden_lista = True

                # --- PUENTE DE NAVEGACIÓN INTUITIVA (Visualización del Botón de Paso) ---
                if st.session_state.get('orden_lista'):
                    st.markdown("---")
                    st.markdown(f"""
                        <div style="background-color: #E8F0FE; padding: 25px; border-radius: 15px; border-left: 8px solid #1E3A8A; box-shadow: 0px 4px 12px rgba(0,0,0,0.1); margin-top: 20px;">
                            <h3 style="color: #1E3A8A; margin-top: 0; font-family: sans-serif;">✅ ANÁLISIS CLÍNICO CONSOLIDADO</h3>
                            <p style="color: #2C3E50; font-size: 1.1rem; line-height: 1.5;">
                                Nexo ha finalizado el mapeo biológico. Para revisar su <b>Protocolo de Transformación</b>, presupuesto y métodos de formalización, proceda al siguiente paso:
                            </p>
                            <div style="background: white; padding: 15px; border-radius: 10px; border: 1px dashed #1E3A8A; text-align: center;">
                                <p style="font-weight: bold; color: #D35400; font-size: 1.2rem; margin: 0;">
                                    ⬅️ DESPLIEGUE EL MENÚ LATERAL (Flecha >)
                                </p>
                                <p style="color: #1E3A8A; font-size: 1.3rem; font-weight: 900; margin: 5px 0;">
                                    Y SELECCIONE: "🏢 Área Administrativa"
                                </p>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("🆘 ¿No encuentra el menú? Haga clic aquí para ayuda"):
                        st.info("En la esquina superior izquierda de su pantalla verá un icono pequeño de flecha (>). Al presionarlo, aparecerán las opciones de la Clínica. Elija 'Área Administrativa'.")

            except Exception as e:
                st.error(f"Error en el núcleo Nexo: {e}")
              
                # CAPTURA TÉCNICA PARA EL EXPEDIENTE ADMINISTRATIVO
                if "CLAVE_ORDEN:" in res:
                    st.session_state.diagnostico_nexo = res.split("CLAVE_ORDEN:")[-1].strip()
                    st.session_state.orden_lista = True
                elif "Área Administrativa" in res and u_turns >= 5:
                    st.session_state.diagnostico_nexo = "Análisis Clínico en Proceso de Transferencia Especializada"
                    st.session_state.orden_lista = True
            except Exception as e:
                st.error(f"Error en el núcleo Nexo: {e}")
        
                # CAPTURA CRÍTICA DEL INFORME PARA ADMINISTRACIÓN
                if "CLAVE_ORDEN:" in res:
                    st.session_state.diagnostico_nexo = res.split("CLAVE_ORDEN:")[-1].strip()
                    st.session_state.orden_lista = True
                elif "Área Administrativa" in res and u_turns >= 5:
                    st.session_state.diagnostico_nexo = "Análisis Clínico en Proceso de Transferencia"
                    st.session_state.orden_lista = True
            except Exception as e:
                st.error(f"Error en el núcleo Nexo: {e}")

# --- MÓDULO: ÁREA ADMINISTRATIVA (VERSIÓN REPARADA ALTA VISIBILIDAD) ---
elif menu == "🏢 Área Administrativa":
    st.title("🏢 Registro y Formalización de Ingreso")
    
    if "orden_lista" in st.session_state and st.session_state.orden_lista:
        diag = st.session_state.get('diagnostico_nexo', 'Evaluación consolidada por Nexo')
        
        # Expediente Clínico de Alta Visibilidad
        st.markdown(f"""
        <div style="background-color: #1E3A8A; padding: 25px; border-radius: 15px; color: white; border-left: 10px solid #FFD700; box-shadow: 0px 4px 10px rgba(0,0,0,0.3);">
            <h3 style="color: #FFD700; margin:0; font-family: sans-serif;">📋 EXPEDIENTE DE INGRESO DIGITAL</h3>
            <p style="font-style: italic; margin-top:10px; color: #ECF0F1; font-size: 1.1rem;">{diag}</p>
            <hr style="border-color: rgba(255,255,255,0.1);">
            <p style="font-size: 0.9rem; color: #BDC3C7;"><b>Protocolo:</b> 4 Sesiones con Terapeutas Humanos. Este informe ha sido derivado al departamento de especialistas.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("---")
        st.subheader("💳 Protocolos de Inversión")
        tab_ve, tab_co, tab_usdt = st.tabs(["🇻🇪 VENEZUELA", "🇨🇴 COLOMBIA", "💎 CRIPTO"])
        
        with tab_ve:
            st.markdown(f"""
                <div style="background-color: #1E3A8A; padding: 25px; border-radius: 15px; border: 2px solid #4682B4; color: white;">
                    <h4 style="color: #FFD700; margin-top: 0;">🇻🇪 Pago Móvil Mercantil</h4>
                    <p style="margin: 5px 0; font-size: 1.1rem;"><b>Documento:</b> V-15.214.337</p>
                    <p style="margin: 5px 0; font-size: 1.1rem;"><b>Teléfono:</b> 04262272765</p>
                    <p style="margin: 5px 0; color: #BDC3C7; font-size: 0.9rem;">Tasa BCV (Euro): {tasa_ve} Bs.</p>
                    <div style="background: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 10px; text-align: center; margin-top: 15px; border: 1px solid rgba(255, 215, 0, 0.4);">
                        <span style="font-size: 0.8rem; color: #FFD700; text-transform: uppercase; letter-spacing: 1px;">Monto a Formalizar</span>
                        <h2 style="margin: 5px 0; color: white; font-size: 2.2rem;">{total_bs:,.2f} Bs.</h2>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with tab_co:
            st.markdown(f"""
                <div style="background-color: #D35400; padding: 25px; border-radius: 15px; border: 2px solid #E67E22; color: white;">
                    <h4 style="color: #FFD700; margin-top: 0;">🇨🇴 Bancolombia / Nequi</h4>
                    <p style="margin: 5px 0; font-size: 1.1rem;"><b>Estado:</b> Próxima apertura de cuenta</p>
                    <p style="margin: 5px 0; font-size: 1.1rem;"><b>Referencia TRM:</b> {tasa_co} COP</p>
                    <div style="background: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 10px; text-align: center; margin-top: 15px; border: 1px solid rgba(255, 215, 0, 0.4);">
                        <span style="font-size: 0.8rem; color: #FFD700; text-transform: uppercase; letter-spacing: 1px;">Monto a Formalizar</span>
                        <h2 style="margin: 5px 0; color: white; font-size: 2.2rem;">{total_cop:,.2f} COP</h2>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with tab_usdt:
            st.markdown(f"""
                <div style="background-color: #145A32; padding: 25px; border-radius: 15px; border: 2px solid #1E8449; color: white;">
                    <h4 style="color: #FFD700; margin-top: 0;">💎 USDT (Red BEP20)</h4>
                    <p style="margin: 5px 0; font-size: 1rem;"><b>Red:</b> Binance Smart Chain (BEP20)</p>
                    <div style="background: rgba(0,0,0,0.3); padding: 10px; border-radius: 8px; margin: 10px 0;">
                        <code style="color: #58D68D; font-size: 0.9rem; word-break: break-all;">0xE30516Af847E0a7E343917e0C204E1e974754dBa</code>
                    </div>
                    <div style="background: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 10px; text-align: center; margin-top: 15px; border: 1px solid rgba(255, 215, 0, 0.4);">
                        <span style="font-size: 0.8rem; color: #FFD700; text-transform: uppercase; letter-spacing: 1px;">Monto a Formalizar</span>
                        <h2 style="margin: 5px 0; color: white; font-size: 2.2rem;">80.00 USDT</h2>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        st.write("---")
        # Botón de WhatsApp con estilo mejorado
        st.markdown(f"""
            <div style="text-align: center;">
                <a href="https://wa.me/584262272765?text=Hola,%20adjunto%20mi%20comprobante%20de%20pago%20para%20formalizar%20mi%20ingreso%20a%20Mind%20Geek%20Clinic." class="btn-whatsapp" style="display: block; width: 100%; text-align: center;">
                    ✅ ENVIAR COMPROBANTE POR WHATSAPP
                </a>
            </div>
        """, unsafe_allow_html=True)
        
        ref = st.text_input("Referencia de pago / Hash de transacción:")
        if st.button("🚀 FINALIZAR Y AGENDAR ESPECIALISTA", use_container_width=True):
            if ref: 
                st.balloons()
                st.success("Registro administrativo completado. Un coordinador de agenda validará su ingreso.")
    else:
        st.warning("⚠️ Requiere evaluación previa por Nexo en la sección de Consulta Médica.")
        
