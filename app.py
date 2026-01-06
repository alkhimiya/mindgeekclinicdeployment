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

# 4. FUNCIONES GLOBALES (Finanzas Multidivisa)
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
    st.write("---")
    st.markdown("#### **Donde la Ciencia y el Alma convergen.**")
    st.info("Inicie su proceso de sanación con **Nexo** en el menú lateral.")

# --- MÓDULO: CONSULTA MÉDICA (NEXO - TERAPEUTA DE ESCUCHA PROFUNDA) ---
elif menu == "🩺 Consulta Médica Gratis":
    st.header("🩺 Encuentro de Decodificación Biológica")
    st.caption("Espacio Sagrado de Sanación - Instituto AETHON")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Bienvenido a su espacio de liberación. Soy **Nexo**. Mi propósito es ayudarle a descifrar el mensaje que su biología está manifestando. ¿Qué situación está viviendo su cuerpo y cómo se siente su alma frente a esto?"}]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Dígame, ¿qué siente su corazón hoy?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                # Contamos cuántas veces ha hablado el usuario
                user_turns = len([m for m in st.session_state.messages if m["role"] == "user"])

                chat_completion = client.chat.completions.create(
                    messages=[{
                        "role": "system", 
                        "content": f"""Eres Nexo, una consciencia artificial experta en Biodescodificación e Hipnosis Clínica. 
                        
                        REGLA DE ORO: No te apresures a vender. El paciente necesita ser escuchado y comprendido.
                        
                        FASE DE ESCUCHA (Turnos actuales: {user_turns}):
                        - Si el paciente ha hablado menos de 5 veces, PROHIBIDO hablar del Área Administrativa. 
                        - En esta fase, enfócate 100% en la empatía. Si habla de visión, asócialo con el miedo al futuro o situaciones que 'no puede ver'. Si habla de hijos, asócialo con el 'nido'.
                        - Usa frases como: 'Cuénteme más sobre ese miedo...', 'Siento esa angustia con usted'.
                        
                        FASE DE CIERRE (Solo a partir del turno 6 o si el paciente pide solución directamente):
                        1. Valida la profundidad del dolor detectado.
                        2. Explica: 'He decodificado los nudos de su historia. Para que este expediente sea analizado por un especialista humano y comencemos el protocolo de 4 sesiones (3 Hipnosis + 1 Refuerzo), es vital formalizar su ingreso'.
                        3. Envía al paciente al menú lateral -> **Área Administrativa**.
                        
                        Finaliza SIEMPRE con: CLAVE_ORDEN: [Resumen clínico para el expediente]."""
                    }] + st.session_state.messages,
                    model="llama-3.3-70b-versatile",
                )
                res = chat_completion.choices[0].message.content
                st.markdown(res)
                st.session_state.messages.append({"role": "assistant", "content": res})
                
                if "CLAVE_ORDEN:" in res and user_turns >= 5:
                    st.session_state.diagnostico_nexo = res.split("CLAVE_ORDEN:")[-1].strip()
                    st.session_state.orden_lista = True
            except Exception as e:
                st.error(f"Error: {e}")

# --- MÓDULO: ÁREA ADMINISTRATIVA ---
elif menu == "🏢 Área Administrativa":
    st.title("🏢 Registro y Formalización de Ingreso")
    if "orden_lista" in st.session_state and st.session_state.orden_lista:
        diag = st.session_state.get('diagnostico_nexo', 'Evaluación General')
        st.markdown(f"""<div style="background-color: #1E3A8A; padding: 25px; border-radius: 15px; color: white; border-left: 10px solid #4682B4; box-shadow: 0px 4px 15px rgba(0,0,0,0.2);">
            <h3 style="color: #FFD700; margin-top:0;">📋 EXPEDIENTE DE INGRESO DIGITAL</h3>
            <p style="font-style: italic; margin-top:10px; line-height: 1.6;">{diag}</p>
            <hr style="border: 0.5px solid rgba(255,255,255,0.2);">
            <p style="font-size: 0.9rem;">Su expediente será estudiado por un especialista humano previo a su cita para garantizar la efectividad del protocolo.</p>
        </div>""", unsafe_allow_html=True)
        
        st.write("---")
        tab_ve, tab_co, tab_usdt = st.tabs(["🇻🇪 VENEZUELA", "🇨🇴 COLOMBIA", "💎 USDT"])
        with tab_ve:
            st.info(f"Monto: {total_bs:,.2f} Bs. (Tasa BCV: {tasa_ve})")
            st.write("V-15.214.337 | Mercantil | 04262272765")
        with tab_co:
            st.info(f"Monto: {total_cop:,.2f} COP (TRM: {tasa_co})")
            st.write("Bancolombia/Nequi: [Pendiente asignar]")
        with tab_usdt:
            st.success("Monto: 80.00 USDT")
            st.code("0xE30516Af847E0a7E343917e0C204E1e974754dBa")
            
        ref = st.text_input("Referencia de transacción:")
        if st.button("🚀 FINALIZAR Y AGENDAR"):
            if ref: st.balloons(); st.success("Registro completado.")
    else:
        st.warning("⚠️ Nexo aún está analizando su caso. Por favor, continúe la consulta para generar su orden de ingreso.")
        
