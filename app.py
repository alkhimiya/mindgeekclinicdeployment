import streamlit as st
import os
import zipfile
import tempfile
from pathlib import Path
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_classic.chains import RetrievalQA
import requests
import json
from datetime import datetime

# ================= CONFIGURACIÓN =================
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")
ZIP_URL = "https://github.com/alkhimiya/mindgeekclinicdeployment/raw/refs/heads/main/mindgeekclinic_db.zip"

# ================= BASE DE DATOS DE PACIENTES =================
def guardar_paciente(datos):
    """Guarda datos del paciente en session_state."""
    if "pacientes" not in st.session_state:
        st.session_state.pacientes = []
    
    datos["fecha"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    datos["id"] = f"{datos['iniciales']}_{len(st.session_state.pacientes)+1:03d}"
    st.session_state.pacientes.append(datos)
    return datos["id"]

# ================= FORMULARIO DIAGNÓSTICO =================
def formulario_diagnostico():
    """Muestra formulario clínico estructurado."""
    st.markdown("### 📋 FORMULARIO DE EVALUACIÓN CLÍNICA")
    
    with st.form("formulario_clinico"):
        col1, col2 = st.columns(2)
        
        with col1:
            iniciales = st.text_input("📝 **Iniciales del nombre**", max_chars=3, 
                                     help="Ej: JPG para Juan Pérez García")
            edad = st.number_input("🎂 **Edad**", min_value=1, max_value=120, value=30)
            estado_civil = st.selectbox(
                "💍 **Estado civil**",
                ["Soltero", "Casado", "Divorciado", "Viudo", "Unión libre", "Separado"]
            )
            
        with col2:
            situacion_laboral = st.selectbox(
                "💼 **Situación laboral**",
                ["Empleado", "Desempleado", "Independiente", "Estudiante", "Jubilado", "Incapacitado"]
            )
            tension_alta = st.number_input("🩺 **Tensión arterial alta (sistólica)**", 
                                          min_value=50, max_value=250, value=120)
            tension_baja = st.number_input("🩺 **Tensión arterial baja (diastólica)**",
                                          min_value=30, max_value=150, value=80)
        
        # Entorno social
        st.markdown("---")
        st.markdown("#### 👥 **ENTORNO SOCIAL**")
        entorno_social = st.text_area(
            "Describa brevemente su entorno social (familia, amigos, relaciones):",
            height=100,
            placeholder="Ej: Vivo solo después de divorcio, tengo 2 hijos que veo fines de semana, pocos amigos cercanos..."
        )
        
        # Dolencia principal
        st.markdown("---")
        st.markdown("#### 🤒 **DOLENCIA / SÍNTOMA PRINCIPAL**")
        dolencia = st.text_area(
            "Describa su dolencia, síntomas y duración:",
            height=120,
            placeholder="Ej: Labios quebradizos desde hace 3 meses, dolor en articulaciones, insomnio..."
        )
        
        # Factores emocionales
        st.markdown("---")
        st.markdown("#### 💭 **FACTORES EMOCIONALES RECIENTES**")
        factores_emocionales = st.text_area(
            "Eventos o situaciones emocionales importantes recientes:",
            height=100,
            placeholder="Ej: Divorcio hace 6 meses, problemas económicos, conflictos familiares..."
        )
        
        # Submit
        submitted = st.form_submit_button("🚀 **ANALIZAR CON BIODESCODIFICACIÓN**", type="primary", use_container_width=True)
        
        if submitted:
            datos_paciente = {
                "iniciales": iniciales.upper(),
                "edad": edad,
                "estado_civil": estado_civil,
                "situacion_laboral": situacion_laboral,
                "tension": f"{tension_alta}/{tension_baja}",
                "entorno_social": entorno_social,
                "dolencia": dolencia,
                "factores_emocionales": factores_emocionales
            }
            
            paciente_id = guardar_paciente(datos_paciente)
            st.session_state.paciente_actual = datos_paciente
            st.session_state.mostrar_diagnostico = True
            st.rerun()

# ================= GENERAR DIAGNÓSTICO =================
def generar_diagnostico_biodescodificacion(sistema, datos_paciente):
    """Genera diagnóstico completo de biodescodificación."""
    
    prompt = f"""
    ## 🧠 DIAGNÓSTICO DE BIODESCODIFICACIÓN - MINDGEEKCLINIC
    
    **DATOS DEL PACIENTE:**
    - Iniciales: {datos_paciente['iniciales']}
    - Edad: {datos_paciente['edad']} años
    - Estado civil: {datos_paciente['estado_civil']}
    - Situación laboral: {datos_paciente['situacion_laboral']}
    - Tensión arterial: {datos_paciente['tension']}
    - Entorno social: {datos_paciente['entorno_social']}
    - Dolencia principal: {datos_paciente['dolencia']}
    - Factores emocionales: {datos_paciente['factores_emocionales']}
    
    **INSTRUCCIONES PARA EL ASISTENTE ESPECIALIZADO:**
    
    1. **DIAGNÓSTICO DE BIODESCODIFICACIÓN:**
       - Analizar la dolencia "{datos_paciente['dolencia']}" según principios de biodescodificación
       - Identificar el conflicto emocional subyacente
       - Relacionar con los factores emocionales reportados
       - Explicar el significado biológico del síntoma
    
    2. **PROTOCOLO TERAPÉUTICO (3 SESIONES):**
       - SESIÓN 1: Enfoque en [conflicto específico]
       - SESIÓN 2: Trabajo en [aspecto emocional]
       - SESIÓN 3: Integración y cierre
    
    3. **PROTOCOLO DE HIPNOSIS:**
       - Frecuencia: 3 veces por semana
       - Duración por sesión: 15-20 minutos
       - Técnicas específicas a aplicar
    
    4. **RECOMENDACIONES ESPECÍFICAS:**
       - Actividades de autohipnosis diarias
       - Ejercicios emocionales
       - Seguimiento recomendado
    
    **GENERAR RESPUESTA ESTRUCTURADA CON:**
    1. Diagnóstico biodescodificación
    2. Conflicto emocional identificado
    3. Protocolo de 3 sesiones
    4. Instrucciones de hipnosis/autohipnosis
    5. Recomendaciones específicas
    
    **RESPUESTA PROFESIONAL:**
    """
    
    try:
        respuesta = sistema.invoke({"query": prompt})
        return respuesta['result']
    except Exception as e:
        return f"Error al generar diagnóstico: {str(e)}"

# ================= SISTEMA PRINCIPAL =================
@st.cache_resource
def cargar_sistema_completo():
    """Carga el sistema RAG con biblioteca especializada."""
    
    if not GROQ_API_KEY:
        st.error("❌ Configura GROQ_API_KEY en Streamlit Secrets.")
        return None
    
    with st.spinner("🔄 Cargando sistema especializado..."):
        try:
            # Descargar biblioteca
            response = requests.get(ZIP_URL, stream=True, timeout=60)
            if response.status_code != 200:
                st.error(f"❌ Error al descargar biblioteca.")
                return None
            
            # Procesar
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "biblioteca.zip")
            extract_path = os.path.join(temp_dir, "biodescodificacion_db")
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            
            # Cargar embeddings
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            vector_store = Chroma(persist_directory=extract_path, embedding_function=embeddings)
            
            # Conectar con IA
            llm = ChatGroq(
                groq_api_key=GROQ_API_KEY,
                model_name="meta-llama/llama-4-scout-17b-16e-instruct",
                temperature=0.3,
                max_tokens=3000
            )
            
            # Crear sistema RAG
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=vector_store.as_retriever(search_kwargs={"k": 8}),
                return_source_documents=True,
                verbose=False
            )
            
            return qa_chain
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)[:150]}")
            return None

# ================= INTERFAZ PRINCIPAL =================
st.set_page_config(
    page_title="MINDGEEKCLINIC - Biodescodificación Profesional",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/271/271226.png", width=80)
    st.markdown("### 🏥 MINDGEEKCLINIC")
    st.markdown("**Sistema Profesional de Biodescodificación**")
    st.markdown("---")
    
    st.markdown("#### 📊 Estadísticas")
    if "pacientes" in st.session_state:
        st.metric("Pacientes atendidos", len(st.session_state.pacientes))
    
    st.markdown("---")
    
    if st.button("🆕 Nuevo Diagnóstico", use_container_width=True, type="primary"):
        st.session_state.mostrar_diagnostico = False
        st.rerun()
    
    if st.button("🔄 Reiniciar Sistema", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()
    
    st.markdown("---")
    st.caption("🧠 Para profesionales de salud mental")

# Título principal
st.title("🧠 MINDGEEKCLINIC")
st.markdown("### **Sistema Profesional de Diagnóstico por Biodescodificación**")
st.markdown("*Para psicólogos, psiquiatras, terapeutas y neuroterapeutas*")
st.markdown("---")

# Inicializar estado
if "mostrar_diagnostico" not in st.session_state:
    st.session_state.mostrar_diagnostico = False
if "paciente_actual" not in st.session_state:
    st.session_state.paciente_actual = None

# Cargar sistema
sistema = cargar_sistema_completo()

if not sistema:
    st.error("⚠️ Sistema no disponible. Verifica configuración.")
    st.stop()

# Mostrar formulario o diagnóstico
if not st.session_state.mostrar_diagnostico:
    formulario_diagnostico()
else:
    # Mostrar datos del paciente
    paciente = st.session_state.paciente_actual
    st.markdown(f"### 📄 **PACIENTE:** {paciente['iniciales']} • {paciente['edad']} años • {paciente['estado_civil']}")
    
    with st.expander("📋 Ver datos completos del paciente"):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Situación laboral:** {paciente['situacion_laboral']}")
            st.write(f"**Tensión arterial:** {paciente['tension']}")
        with col2:
            st.write(f"**Entorno social:** {paciente['entorno_social'][:100]}...")
            st.write(f"**Factores emocionales:** {paciente['factores_emocionales'][:100]}...")
    
    # Generar diagnóstico
    st.markdown("---")
    st.markdown("### 🔬 **DIAGNÓSTICO DE BIODESCODIFICACIÓN**")
    
    with st.spinner("🔄 Analizando con biblioteca especializada..."):
        diagnostico = generar_diagnostico_biodescodificacion(sistema, paciente)
        
        # Mostrar diagnóstico
        st.markdown(diagnostico)
        
        # Opciones de hipnosis
        st.markdown("---")
        st.markdown("### 🎧 **PROTOCOLO DE HIPNOSIS PERSONALIZADO**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🎯 **Para aplicación por terapeuta:**")
            st.info("""
            **Protocolo sugerido:**
            1. **Sesión 1:** Identificación del conflicto
            2. **Sesión 2:** Reprogramación emocional  
            3. **Sesión 3:** Integración y cierre
            
            **Frecuencia:** 3 veces por semana
            **Duración:** 15-20 minutos por sesión
            """)
            
            if st.button("📝 Generar guión completo para terapeuta", use_container_width=True):
                st.session_state.generar_guion = True
        
        with col2:
            st.markdown("#### 🎵 **Para autohipnosis (grabación):**")
            st.info("""
            **Instrucciones para el paciente:**
            1. Grabar en dispositivo de audio
            2. Escuchar 3 veces por semana
            3. Ambiente tranquilo, posición cómoda
            4. Seguir instrucciones de respiración
            
            **Duración recomendada:** 12-15 minutos
            """)
            
            if st.button("🎤 Generar guión para grabación", use_container_width=True):
                st.session_state.generar_grabacion = True
        
        # Botón para nuevo diagnóstico
        st.markdown("---")
        if st.button("🆕 Realizar nuevo diagnóstico", use_container_width=True, type="primary"):
            st.session_state.mostrar_diagnostico = False
            st.rerun()

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.8em;'>
    🧠 <b>MINDGEEKCLINIC v5.0</b> • Sistema profesional de biodescodificación • 
    Para uso de profesionales de salud mental debidamente capacitados
    </div>
    """,
    unsafe_allow_html=True
)
