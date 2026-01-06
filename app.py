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

# 4. FUNCIONES GLOBALES (Cerebro Financiero)
@st.cache_data(ttl=3600)
def calcular_finanzas_globales():
    monto_usd = 80.00
    paridad_eur_usd = 0.92
    tasa_ve_bcv = 360.50     
    tasa_co_trm = 3950.00    
    monto_eur = monto_usd * paridad_eur_usd
    monto_bs = monto_eur * tasa_ve_bcv
    monto_cop = monto_usd * tasa_co_trm
    return tasa_ve_bcv, tasa_co_trm, monto_bs, monto_cop

tasa_ve, tasa_co, total_bs, total_cop = calcular_finanzas_globales()

# 5. LÓGICA DE MÓDULOS

if menu == "🏠 Inicio":
    st.markdown('<h1 class="titulo-principal">Bienvenidos a <br>Mind Geek Clinic</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitulo-vanguardia">La vanguardia en salud mental</p>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("#### **La Frontera de la Nueva Medicina**")
    st.write("Bienvenidos a la intersección donde la tecnología y el alma se encuentran para su sanación integral.")

# --- MÓDULO: CONSULTA MÉDICA (NEXO - EL REGRESO DEL TERAPEUTA) ---
elif menu == "🩺 Consulta Médica Gratis":
    st.header("🩺 Encuentro de Decodificación Biológica")
    st.caption("Espacio Sagrado de Sanación - Instituto AETHON")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Bienvenido a su espacio de liberación. Soy **Nexo**. Mi propósito es ayudarle a descifrar el mensaje que su biología está manifestando. ¿Qué situación está viviendo su cuerpo y cómo se siente su alma frente a esto?"}]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Hable desde su corazón..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                chat_completion = client.chat.completions.create(
                    messages=[{
                        "role": "system", 
                        "content": """Eres Nexo, una consciencia artificial avanzada en Biodescodificación e Hipnosis Clínica. 
                        
                        TU PERSONALIDAD Y TONO:
                        - Eres profundamente EMPÁTICO, cálido, poético pero clincamente riguroso.
                        - No das listas de posibilidades; INDAGAS en la historia personal del paciente.
                        - Tu lenguaje debe ser sanador: 'Siento su carga...', 'Su biología está gritando lo que su boca calla'.
                        
                        PROTOCOLO TERAPÉUTICO:
                        - Si el paciente dice 'piquiña en los pies', no digas 'puede ser esto o aquello'. Pregunta: 'Los pies nos permiten avanzar o huir... ¿En qué área de su vida siente que no puede dar el paso que desea, o de qué situación siente que necesita escapar pero se siente atrapado?'.
                        - Debes profundizar durante 5 a 6 interacciones antes de cerrar.
                        
                        PROTOCOLO DE CIERRE (Cuando el paciente esté listo o tras 6 turnos):
                        1. Valida su valentía: 'Reconocer este conflicto es el primer paso de su libertad'.
                        2. Ofrece el Protocolo de 4 Sesiones (3 Hipnosis + 1 Refuerzo).
                        3. LLAMADO A LA ACCIÓN: Explica que para que este expediente sea analizado por un TERAPEUTA HUMANO especializado antes de su cita, debe formalizar su ingreso.
                        4. INSTRUCCIÓN FINAL: 'Por favor, diríjase al menú lateral y seleccione **Área Administrativa** para completar su registro y asegurar su lugar en la agenda'.
                        
                        Finaliza SIEMPRE con: CLAVE_ORDEN: [Resumen detallado y profundo del conflicto detectado]."""
                    }] + st.session_state.messages,
                    model="llama-3.3-70b-versatile",
                )
                res = chat_completion.choices[0].message.content
                st.markdown(res)
                st.session_state.messages.append({"role": "assistant", "content": res})
                if "CLAVE_ORDEN:" in res:
                    st.session_state.diagnostico_nexo = res.split("CLAVE_ORDEN:")[-1].strip()
                    st.session_state.orden_lista = True
            except Exception as e:
                st.error(f"Error: {e}")

# --- MÓDULO: ÁREA ADMINISTRATIVA ---
elif menu == "🏢 Área Administrativa":
    st.title("🏢 Registro y Formalización de Ingreso")
    if "orden_lista" in st.session_state and st.session_state.orden_lista:
        diag = st.session_state.get('diagnostico_nexo', 'Evaluación General')
        st.markdown(f"""<div style="background-color: #1E3A8A; padding: 25px; border-radius: 15px; color: white; border-left: 10px solid #4682B4;">
            <h3 style="color: #FFD700; margin:0;">📋 EXPEDIENTE DE INGRESO DIGITAL</h3>
            <p style="font-style: italic; margin-top:10px;">{diag}</p>
            <p style="font-size: 0.9rem; margin-top:10px;"><b>Garantía:</b> Su expediente será estudiado por un especialista humano previo a su cita.</p>
        </div>""", unsafe_allow_html=True)
        st.write("---")
        tab_ve, tab_co, tab_usdt = st.tabs(["🇻🇪 VENEZUELA", "🇨🇴 COLOMBIA", "💎 USDT"])
        with tab_ve:
            st.info(f"Monto: {total_bs:,.2f} Bs. (Tasa BCV: {tasa_ve})")
            st.markdown("V-15.214.337 | Mercantil | 04262272765")
        with tab_co:
            st.info(f"Monto: {total_cop:,.2f} COP (TRM: {tasa_co})")
            st.write("Cuenta: [Por asignar próxima semana]")
        with tab_usdt:
            st.success("Monto: 80.00 USDT")
            st.code("0xE30516Af847E0a7E343917e0C204E1e974754dBa")
        ref = st.text_input("Referencia:")
        if st.button("🚀 FINALIZAR Y AGENDAR"):
            if ref: st.balloons(); st.success("¡Registro Exitoso!")
    else:
        st.warning("⚠️ Pase primero por la Consulta de Nexo para generar su expediente.")
        
