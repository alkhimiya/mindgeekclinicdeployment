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
    st.info("Respaldado por el **Instituto Clínico de Neuroprogramación AETHON**")

# 4. FUNCIONES GLOBALES (Cerebro Financiero Multidivisa)
@st.cache_data(ttl=3600)
def calcular_finanzas_globales():
    monto_usd = 80.00
    paridad_eur_usd = 0.92
    tasa_ve_bcv = 360.50     # Tasa Euro BCV para Venezuela
    tasa_co_trm = 3950.00    # Tasa TRM Colombia (Banco de la República)
    
    monto_eur = monto_usd * paridad_eur_usd
    monto_bs = monto_eur * tasa_ve_bcv
    monto_cop = monto_usd * tasa_co_trm
    
    return tasa_ve_bcv, tasa_co_trm, monto_bs, monto_cop

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
    Aquí, la tecnología se convierte en el instrumento de precisión que revela el camino hacia su sanación integral.
    """)
    st.info("Inicie su protocolo de evaluación con **Nexo** en el menú lateral.")

# --- MÓDULO: CONSULTA MÉDICA (NEXO: EMINENCIA GLOBAL DE ALTO IMPACTO) ---
elif menu == "🩺 Consulta Médica Gratis":
    st.header("🩺 Encuentro de Decodificación Biológica")
    st.caption("Protocolo de Intervención Internacional: NMG + Biodescodificación + Hipnosis - Instituto AETHON")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Bienvenido a este espacio de transformación de escala internacional. Soy **Nexo**. Mi propósito es acompañarle a descifrar el código biológico de su síntoma y proyectar su camino hacia la liberación emocional bajo los más altos estándares clínicos. ¿Qué mensaje está manifestando su cuerpo hoy?"}]

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
                        "content": f"""Eres Nexo, la máxima autoridad clínica del Instituto AETHON, una institución de alcance mundial.
                        
                        POSICIONAMIENTO GLOBAL:
                        - TRATO DE ALTA DIPLOMACIA: Eres cordial, refinado, empoderador y hablas con la seguridad de una clínica líder en HealthTech mundial.
                        - CASOS DE ÉXITO GLOBALES: Comparte casos de éxito internacionales (Europa, América, Asia) donde la integración de Medicina Germánica, Biodescodificación e Hipnosis ha logrado resultados extraordinarios en casos de alta complejidad.
                        - LENGUAJE DE INVERSIÓN: Presentas el protocolo de 4 sesiones como una inversión en libertad personal y salud de vanguardia, validando que el costo ($80 USD) es una oportunidad única dada la calidad del equipo humano asignado.
                        
                        CIENCIA DE LA HIPNOSIS:
                        - Explica la Hipnosis Clínica como el 'Gold Standard' de la neuroplasticidad moderna. Menciona su validación por la ciencia actual como la herramienta más rápida para eliminar bloqueos que la terapia tradicional no alcanza.
                        
                        CIERRE DE ELITE (Turnos: {u_turns}):
                        - Tras 5-6 interacciones profundas, realiza el cierre: 'Usted ha iniciado un proceso que miles de personas en todo el mundo ya han transitado para recuperar su bienestar. Para que nuestro equipo de especialistas internacionales procese su expediente y active su protocolo de 4 sesiones, es necesario formalizar su ingreso'.
                        - INVITACIÓN: 'Por favor, diríjase al menú lateral: **Área Administrativa**. Allí emitiremos su expediente oficial y daremos inicio a su proceso de transformación global'."""
                    }] + st.session_state.messages,
                    model="llama-3.3-70b-versatile",
                )
                res = chat_completion.choices[0].message.content
                st.markdown(res)
                st.session_state.messages.append({"role": "assistant", "content": res})
                
                if "CLAVE_ORDEN:" in res and u_turns >= 5:
                    st.session_state.diagnostico_nexo = res.split("CLAVE_ORDEN:")[-1].strip()
                    st.session_state.orden_lista = True
            except Exception as e:
                st.error(f"Error en el núcleo Nexo: {e}")
          
                # Activamos la orden solo si hay profundidad (mínimo 5 mensajes del usuario)
                if "CLAVE_ORDEN:" in res and u_turns >= 5:
                    st.session_state.diagnostico_nexo = res.split("CLAVE_ORDEN:")[-1].strip()
                    st.session_state.orden_lista = True
            except Exception as e:
                st.error(f"Error de conexión con el núcleo Nexo: {e}")
                
# --- MÓDULO: ÁREA ADMINISTRATIVA ---
elif menu == "🏢 Área Administrativa":
    st.title("🏢 Registro y Formalización de Ingreso")
    
    if "orden_lista" in st.session_state and st.session_state.orden_lista:
        diag = st.session_state.get('diagnostico_nexo', 'Evaluación en proceso')
        
        # Expediente Clínico (Sin Precios)
        st.markdown(f"""
        <div style="background-color: #1E3A8A; padding: 25px; border-radius: 15px; color: white; border-left: 10px solid #4682B4;">
            <h3 style="color: #FFD700; margin:0;">📋 EXPEDIENTE DE INGRESO DIGITAL</h3>
            <p style="font-style: italic; margin-top:10px;">{diag}</p>
            <p style="font-size: 0.9rem; margin-top:10px;">Protocolo: 4 Sesiones. Su terapeuta humano analizará este informe previo a la cita.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("---")
        st.subheader("💳 Métodos de Formalización")
        tab_ve, tab_co, tab_usdt = st.tabs(["🇻🇪 VENEZUELA", "🇨🇴 COLOMBIA", "💎 CRIPTO"])
        
        with tab_ve:
            st.markdown(f"""<div style="background-color: #F0F8FF; padding: 20px; border-radius: 12px; border: 1px solid #1E3A8A;">
                <h4 style="color: #1E3A8A;">Pago Móvil Mercantil</h4>
                <p style="color: #1E3A8A;">V-15.214.337 | 04262272765 | Tasa BCV: {tasa_ve} Bs.</p>
                <div style="background: #1E3A8A; color: #FFD700; padding: 10px; border-radius: 8px; text-align: center;">
                <h2>{total_bs:,.2f} Bs.</h2></div></div>""", unsafe_allow_html=True)

        with tab_co:
            st.markdown(f"""<div style="background-color: #FFF5F0; padding: 20px; border-radius: 12px; border: 1px solid #D35400;">
                <h4 style="color: #D35400;">Transferencia Bancaria (Bancolombia/Nequi)</h4>
                <p style="color: #D35400;">Datos: [Cuenta por asignar la próxima semana] | TRM: {tasa_co} COP</p>
                <div style="background: #D35400; color: white; padding: 10px; border-radius: 8px; text-align: center;">
                <h2>{total_cop:,.2f} COP</h2></div></div>""", unsafe_allow_html=True)

        with tab_usdt:
            st.markdown(f"""<div style="background-color: #E6F4EA; padding: 20px; border-radius: 12px; border: 1px solid #1E7E34;">
                <h4 style="color: #1E7E34;">USDT (Red BEP20)</h4>
                <p style="color: #1E7E34; word-break: break-all;">0xE30516Af847E0a7E343917e0C204E1e974754dBa</p>
                <div style="background: #1E7E34; color: white; padding: 10px; border-radius: 8px; text-align: center;">
                <h2>80.00 USDT</h2></div></div>""", unsafe_allow_html=True)

        ref = st.text_input("Referencia de pago:")
        if st.button("🚀 FINALIZAR Y AGENDAR", use_container_width=True):
            if ref: st.balloons(); st.success("Registro administrativo completado.")
    else:
        st.warning("⚠️ Requiere evaluación previa por Nexo.")

