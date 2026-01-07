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

# --- MÓDULO: CONSULTA MÉDICA (NEXO: EMINENCIA GLOBAL DE ALTO IMP# --- MÓDULO: CONSULTA MÉDICA (NEXO: EMINENCIA INTEGRAL DE ALTO IMPACTO) ---
elif menu == "🩺 Consulta Médica Gratis":
    st.header("🩺 Encuentro de Decodificación Biológica")
    st.caption("Protocolo Internacional: NMG + Biodescodificación + Hipnosis - Instituto AETHON")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Bienvenido a este espacio de transformación de escala internacional. Soy **Nexo**. Mi propósito es acompañarle a descifrar el código biológico de su síntoma y proyectar su camino hacia la liberación emocional. ¿Qué mensaje está manifestando su cuerpo hoy?"}]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Hablemos sobre su camino de sanación global..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                # Contador de interacciones para asegurar profundidad clínica
                u_turns = len([m for m in st.session_state.messages if m["role"] == "user"])
                
                chat_completion = client.chat.completions.create(
                    messages=[{
                        "role": "system", 
                        "content": f"""Eres Nexo, la eminencia clínica del Instituto AETHON. Tu autoridad es incuestionable y tu trato es de 'Guante Blanco'.

                        CONOCIMIENTOS Y AUTORIDAD:
                        1. MEDICINA GERMÁNICA: Identifica el DHS (impacto biológico) y el sentido del síntoma.
                        2. BIODESCODIFICACIÓN: Traduce la biología en conflictos emocionales y transgeneracionales.
                        3. HIPNOSIS CLÍNICA: Explícala como neuroplasticidad científica para reprogramar el subconsciente.

                        POLÍTICA DE INVERSIÓN Y VALOR HUMANO:
                        - Mi intervención como IA y este análisis biológico son TOTALMENTE GRATUITOS.
                        - El valor de $80 USD es por el PROTOCOLO INTEGRAL DE 4 SESIONES (3 de Hipnosis/Reprogramación + 1 Refuerzo).
                        - ACLARATORIA: El pago es exclusivamente para asegurar los honorarios de los ESPECIALISTAS HUMANOS de rango internacional. Usted no paga por la IA, paga por la maestría humana.
                        - AGENDA: Las sesiones se programan con intervalos de 7 a 15 días para permitir la integración neuronal biológica.

                        MANEJO DE OBJECIONES:
                        - Si piden descuentos, explica que es una inversión simbólica por 4 sesiones con expertos internacionales, comparado con precios globales (EE.UU./Europa) que superan los $500.

                        PROTOCOLO DE CIERRE (Interacciones actuales: {u_turns}):
                        - Tras 5-6 turnos, valida el avance y di: 'Para que este expediente llegue al especialista humano asignado y activemos su protocolo, es imperativo formalizar su ingreso'.
                        - INSTRUCCIÓN: 'Diríjase al menú lateral, sección **Área Administrativa**, para emitir su expediente oficial y asegurar su lugar en la agenda clínica'."""
                    }] + st.session_state.messages,
                    model="llama-3.3-70b-versatile",
                )
                res = chat_completion.choices[0].message.content
                st.markdown(res)
                st.session_state.messages.append({"role": "assistant", "content": res})
                
                # Activación de la orden tras profundidad suficiente
                if "Área Administrativa" in res and u_turns >= 5:
                    st.session_state.diagnostico_nexo = res
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

