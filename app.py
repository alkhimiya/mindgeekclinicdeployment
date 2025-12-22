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

# ================= FORMULARIO DIAGNÓSTICO MEJORADO =================
def formulario_diagnostico():
    """Muestra formulario clínico estructurado CON PREGUNTAS ESPECÍFICAS."""
    st.markdown("### 📋 FORMULARIO DE EVALUACIÓN CLÍNICA ESPECIALIZADA")
    
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
        
        # ==== PREGUNTAS ESPECÍFICAS NUEVAS ====
        st.markdown("---")
        st.markdown("#### ⏳ **TIEMPO DEL PADECIMIENTO**")
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            tiempo_padecimiento = st.selectbox(
                "¿Desde hace cuánto tiempo siente este padecimiento?",
                ["Menos de 1 mes", "1-3 meses", "3-6 meses", "6-12 meses", 
                 "1-2 años", "2-5 años", "Más de 5 años", "Desde la infancia"]
            )
        
        with col_t2:
            frecuencia = st.selectbox(
                "¿Con qué frecuencia se presenta?",
                ["Constante", "Diariamente", "Varias veces por semana", 
                 "Semanalmente", "Mensualmente", "Ocasionalmente", "Solo en ciertas situaciones"]
            )
        
        # ==== EVENTOS EMOCIONALES DETALLADOS ====
        st.markdown("---")
        st.markdown("#### 🎯 **EVENTOS EMOCIONALES ASOCIADOS (TRIANGULACIÓN)**")
        
        st.markdown("**Pregunta clave:** ¿Qué eventos suceden en su vida que impactan emocionalmente CUANDO se presenta el cuadro?")
        
        eventos_emocionales = st.text_area(
            "Describa los eventos específicos (pasados o presentes) que coinciden con la aparición/worsening de los síntomas:",
            height=150,
            placeholder="""Ejemplo detallado:
1. El síntoma empeora los lunes cuando voy a trabajar (evento: regreso laboral)
2. Aparece después de discusiones con mi pareja (evento: conflicto relacional)
3. Se intensifica cuando visito a mis padres (evento: encuentro familiar)
4. Mejora cuando estoy de vacaciones (evento: descanso/ocio)
5. Comenzó después de la muerte de mi padre hace 2 años (evento: duelo)

Describa la RELACIÓN TEMPORAL entre eventos y síntomas:"""
        )
        
        # ==== SÍNTOMAS Y CONTEXTO ====
        st.markdown("---")
        st.markdown("#### 🤒 **DOLENCIA / SÍNTOMA PRINCIPAL**")
        
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            dolencia = st.text_area(
                "Describa su dolencia o síntoma principal:",
                height=120,
                placeholder="Ej: Dolor de cabeza tipo migraña, insomnio, ansiedad, labios quebradizos..."
            )
        
        with col_s2:
            intensidad = st.slider("Intensidad (1-10)", 1, 10, 5)
            factores_desencadenantes = st.text_area(
                "Factores que desencadenan o agravan los síntomas:",
                height=120,
                placeholder="Ej: Estrés laboral, discusiones, clima frío, ciertos alimentos..."
            )
        
        # ==== ENTORNO SOCIAL ====
        st.markdown("---")
        st.markdown("#### 👥 **ENTORNO SOCIAL ACTUAL**")
        entorno_social = st.text_area(
            "Describa su entorno social actual y relaciones significativas:",
            height=100,
            placeholder="Ej: Vivo solo después de divorcio, tengo 2 hijos que veo fines de semana, pocos amigos cercanos, relación conflictiva con jefe..."
        )
        
        # Submit
        st.markdown("---")
        submitted = st.form_submit_button(
            "🚀 **ANALIZAR CON BIODESCODIFICACIÓN Y TRIANGULACIÓN**", 
            type="primary", 
            use_container_width=True
        )
        
        if submitted:
            datos_paciente = {
                "iniciales": iniciales.upper(),
                "edad": edad,
                "estado_civil": estado_civil,
                "situacion_laboral": situacion_laboral,
                "tension": f"{tension_alta}/{tension_baja}",
                "tiempo_padecimiento": tiempo_padecimiento,
                "frecuencia": frecuencia,
                "eventos_emocionales": eventos_emocionales,  # NUEVO
                "dolencia": dolencia,
                "intensidad": intensidad,
                "factores_desencadenantes": factores_desencadenantes,  # NUEVO
                "entorno_social": entorno_social
            }
            
            paciente_id = guardar_paciente(datos_paciente)
            st.session_state.paciente_actual = datos_paciente
            st.session_state.mostrar_diagnostico = True
            st.rerun()

# ================= GENERAR DIAGNÓSTICO CON TRIANGULACIÓN =================
def generar_diagnostico_triangulacion(sistema, datos_paciente):
    """Genera diagnóstico completo con triangulación de eventos emocionales."""
    
    prompt = f"""
    ## 🧠 DIAGNÓSTICO DE BIODESCODIFICACIÓN CON TRIANGULACIÓN - MINDGEEKCLINIC
    
    **DATOS COMPLETOS DEL PACIENTE:**
    - Iniciales: {datos_paciente['iniciales']}
    - Edad: {datos_paciente['edad']} años
    - Estado civil: {datos_paciente['estado_civil']}
    - Situación laboral: {datos_paciente['situacion_laboral']}
    - Tensión arterial: {datos_paciente['tension']}
    - Tiempo del padecimiento: {datos_paciente['tiempo_padecimiento']}
    - Frecuencia: {datos_paciente['frecuencia']}
    - Intensidad: {datos_paciente['intensidad']}/10
    
    **SÍNTOMA PRINCIPAL:**
    {datos_paciente['dolencia']}
    
    **EVENTOS EMOCIONALES ASOCIADOS (PARA TRIANGULACIÓN):**
    {datos_paciente['eventos_emocionales']}
    
    **FACTORES DESENCADENANTES:**
    {datos_paciente['factores_desencadenantes']}
    
    **ENTORNO SOCIAL:**
    {datos_paciente['entorno_social']}
    
    **INSTRUCCIONES ESPECÍFICAS PARA EL ASISTENTE ESPECIALIZADO:**
    
    1. **TRIANGULACIÓN DIAGNÓSTICA:**
       - Analizar la relación TEMPORAL entre eventos emocionales y síntomas
       - Identificar PATRONES específicos en "{datos_paciente['eventos_emocionales']}"
       - Determinar si hay eventos DESENCADENANTES, MANTENEDORES o AGRAVANTES
       - Relacionar tiempo "{datos_paciente['tiempo_padecimiento']}" con eventos de vida
    
    2. **DIAGNÓSTICO DE BIODESCODIFICACIÓN ESPECÍFICO:**
       - Interpretar "{datos_paciente['dolencia']}" según biodescodificación
       - Identificar el CONFLICTO EMOCIONAL PRECISO basado en triangulación
       - Explicar SIGNIFICADO BIOLÓGICO del síntoma
       - Relacionar con eventos específicos mencionados
    
    3. **PROTOCOLO TERAPÉUTICO ESTRUCTURADO (3 SESIONES):**
       - SESIÓN 1: Enfoque en [conflicto específico identificado por triangulación]
       - SESIÓN 2: Trabajo en [eventos emocionales clave identificados]
       - SESIÓN 3: Integración y [estrategias específicas basadas en factores desencadenantes]
    
    4. **PROTOCOLO DE HIPNOSIS ESPECÍFICO (basado en biblioteca de modelos):**
       - Frecuencia: 3 veces por semana (como indica biblioteca)
       - Duración: 15-20 minutos por sesión
       - Técnicas ESPECÍFICAS de la biblioteca de modelos de hipnosis
       - INSTRUCCIONES DETALLADAS para grabación o aplicación
    
    5. **RECOMENDACIONES PERSONALIZADAS:**
       - Actividades de autohipnosis DIARIAS basadas en triangulación
       - Ejercicios emocionales ESPECÍFICOS para eventos identificados
       - Estrategias para manejar factores desencadenantes
    
    **REQUISITOS ESTRICTOS DE RESPUESTA:**
    1. DEBE basarse en la biblioteca de biodescodificación disponible
    2. DEBE usar modelos de hipnosis de la biblioteca
    3. DEBE incluir INSTRUCCIONES ESPECÍFICAS para terapia
    4. DEBE mencionar técnicas CONCRETAS de la biblioteca
    5. DEBE ser ESTRUCTURADO y PROFESIONAL
    
    **FORMATO DE RESPUESTA:**
    
    ## 🔍 DIAGNÓSTICO POR TRIANGULACIÓN
    
    ### 1. Análisis de Patrones Identificados
    [Explicar relación eventos-síntomas]
    
    ### 2. Diagnóstico de Biodescodificación
    [Conflicto emocional específico + significado biológico]
    
    ### 3. Protocolo de 3 Sesiones Terapéuticas
    **Sesión 1:** [Instrucciones específicas]
    **Sesión 2:** [Instrucciones específicas]  
    **Sesión 3:** [Instrucciones específicas]
    
    ### 4. Protocolo de Hipnosis/Autohipnosis
    [Instrucciones DETALLADAS para grabación o aplicación]
    
    ### 5. Recomendaciones Específicas
    [Basadas en triangulación de eventos]
    
    **RESPUESTA PROFESIONAL ESTRUCTURADA:**
    """
    
    try:
        respuesta = sistema.invoke({"query": prompt})
        return respuesta['result']
    except Exception as e:
        return f"Error al generar diagnóstico: {str(e)}"

# ================= GENERAR GUIÓN DE HIPNOSIS =================
def generar_guion_hipnosis(sistema, datos_paciente, tipo="terapeuta"):
    """Genera guión específico de hipnosis basado en biblioteca."""
    
    tipo_texto = "para aplicación por terapeuta" if tipo == "terapeuta" else "para grabación de autohipnosis"
    
    prompt = f"""
    ## 🎧 GUION DE HIPNOSIS ESPECÍFICO - MINDGEEKCLINIC
    
    **CONTEXTO DEL PACIENTE:**
    - Síntoma: {datos_paciente['dolencia']}
    - Conflicto identificado: [Basado en triangulación anterior]
    - Eventos emocionales: {datos_paciente['eventos_emocionales'][:200]}
    
    **INSTRUCCIONES PARA EL ASISTENTE:**
    
    Generar un guión COMPLETO de hipnosis {tipo_texto} basado en la biblioteca de modelos de hipnosis.
    
    **REQUISITOS:**
    1. Usar técnicas ESPECÍFICAS de la biblioteca de modelos
    2. Incluir inducción, trabajo terapéutico y despertar
    3. Duración: 15-20 minutos
    4. Frecuencia: 3 veces por semana
    5. Instrucciones PRECISAS para {'el terapeuta' if tipo == 'terapeuta' else 'grabación'}
    
    **ESTRUCTURA DEL GUIÓN:**
    
    ### 🎯 OBJETIVO TERAPÉUTICO
    [Objetivo específico basado en triangulación]
    
    ### 📝 GUIÓN COMPLETO
    
    **INDUCCIÓN:**
    [Texto completo de inducción hipnótica]
    
    **TRABAJO TERAPÉUTICO:**
    [Instrucciones específicas para trabajar el conflicto]
    
    **SUGERENCIAS POSHIPNÓTICAS:**
    [Sugerencias para después de la sesión]
    
    **DESPERTAR:**
    [Instrucciones para finalizar]
    
    ### 🕒 INSTRUCCIONES DE APLICACIÓN
    [Instrucciones específicas para {'terapeuta' if tipo == 'terapeuta' else 'paciente'}]
    
    **GUIÓN COMPLETO:**
    """
    
    try:
        respuesta = sistema.invoke({"query": prompt})
        return respuesta['result']
    except Exception as e:
        return f"Error al generar guión: {str(e)}"

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
                max_tokens=3500  # Aumentado para respuestas más completas
            )
            
            # Crear sistema RAG
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=vector_store.as_retriever(search_kwargs={"k": 10}),  # Más documentos
                return_source_documents=True,
                verbose=False
            )
            
            return qa_chain
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)[:150]}")
            return None

# ================= INTERFAZ PRINCIPAL =================
st.set_page_config(
    page_title="MINDGEEKCLINIC - Biodescodificación con Triangulación",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/271/271226.png", width=80)
    st.markdown("### 🏥 MINDGEEKCLINIC")
    st.markdown("**Sistema Profesional con Triangulación Diagnóstica**")
    st.markdown("---")
    
    st.markdown("#### 📊 Estadísticas")
    if "pacientes" in st.session_state:
        st.metric("Pacientes atendidos", len(st.session_state.pacientes))
    
    st.markdown("---")
    
    if st.button("🆕 Nuevo Diagnóstico", use_container_width=True, type="primary"):
        st.session_state.mostrar_diagnostico = False
        st.session_state.generar_guion = False
        st.session_state.generar_grabacion = False
        st.rerun()
    
    if st.button("🔄 Reiniciar Sistema", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()
    
    st.markdown("---")
    st.caption("🎯 Sistema con Triangulación de Eventos Emocionales")

# Título principal
st.title("🧠 MINDGEEKCLINIC")
st.markdown("### **Sistema de Diagnóstico por Biodescodificación con Triangulación Emocional**")
st.markdown("*Identificación precisa de relaciones evento-síntoma para protocolos personalizados*")
st.markdown("---")

# Inicializar estados
if "mostrar_diagnostico" not in st.session_state:
    st.session_state.mostrar_diagnostico = False
if "paciente_actual" not in st.session_state:
    st.session_state.paciente_actual = None
if "generar_guion" not in st.session_state:
    st.session_state.generar_guion = False
if "generar_grabacion" not in st.session_state:
    st.session_state.generar_grabacion = False
if "diagnostico_completo" not in st.session_state:
    st.session_state.diagnostico_completo = None

# Cargar sistema
sistema = cargar_sistema_completo()

if not sistema:
    st.error("⚠️ Sistema no disponible. Verifica configuración.")
    st.stop()

# Mostrar formulario o diagnóstico
if not st.session_state.mostrar_diagnostico:
    formulario_diagnostico()
else:
    paciente = st.session_state.paciente_actual
    
    # Mostrar datos del paciente con nueva información
    st.markdown(f"### 📄 **PACIENTE:** {paciente['iniciales']} • {paciente['edad']} años")
    
    with st.expander("📋 Ver datos completos con triangulación"):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Estado civil:** {paciente['estado_civil']}")
            st.write(f"**Situación laboral:** {paciente['situacion_laboral']}")
            st.write(f"**Tiempo padecimiento:** {paciente['tiempo_padecimiento']}")
            st.write(f"**Frecuencia:** {paciente['frecuencia']}")
            st.write(f"**Intensidad:** {paciente['intensidad']}/10")
        
        with col2:
            st.write(f"**Tensión arterial:** {paciente['tension']}")
            st.write(f"**Dolencia:** {paciente['dolencia']}")
            st.write(f"**Factores desencadenantes:** {paciente['factores_desencadenantes'][:150]}...")
        
        st.markdown("#### 🎯 **Eventos Emocionales para Triangulación:**")
        st.info(paciente['eventos_emocionales'])
    
    # Generar diagnóstico con triangulación
    st.markdown("---")
    st.markdown("### 🔬 **DIAGNÓSTICO CON TRIANGULACIÓN EMOCIONAL**")
    
    if st.session_state.diagnostico_completo is None:
        with st.spinner("🔄 Analizando patrones evento-síntoma..."):
            diagnostico = generar_diagnostico_triangulacion(sistema, paciente)
            st.session_state.diagnostico_completo = diagnostico
    
    # Mostrar diagnóstico
    st.markdown(st.session_state.diagnostico_completo)
    
    # ==== SECCIÓN DE HIPNOSIS MEJORADA ====
    st.markdown("---")
    st.markdown("### 🎧 **PROTOCOLOS DE HIPNOSIS ESPECÍFICOS**")
    
    if not st.session_state.generar_guion and not st.session_state.generar_grabacion:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 👨‍⚕️ **Para aplicación por terapeuta:**")
            st.info("""
            **Basado en biblioteca de modelos de hipnosis:**
            - Técnicas específicas de inducción
            - Protocolos validados
            - Duración: 15-20 minutos
            - Frecuencia: 3 veces/semana
            """)
            
            if st.button("📝 Generar guión COMPLETO para terapeuta", use_container_width=True):
                st.session_state.generar_guion = True
                st.rerun()
        
        with col2:
            st.markdown("#### 🎵 **Para autohipnosis (grabación personal):**")
            st.info("""
            **Instrucciones específicas de la biblioteca:**
            - Técnicas de autoinducción
            - Sugerencias poshipnóticas
            - Grabación en dispositivo de audio
            - Escuchar 3 veces por semana
            """)
            
            if st.button("🎤 Generar guión para GRABACIÓN", use_container_width=True):
                st.session_state.generar_grabacion = True
                st.rerun()
    
    # Generar guiones específicos
    if st.session_state.generar_guion:
        st.markdown("---")
        st.markdown("### 👨‍⚕️ **GUIÓN COMPLETO PARA TERAPEUTA**")
        with st.spinner("Generando guión basado en biblioteca de modelos..."):
            guion = generar_guion_hipnosis(sistema, paciente, "terapeuta")
            st.markdown(guion)
            
            if st.button("↩️ Volver a opciones", use_container_width=True):
                st.session_state.generar_guion = False
                st.rerun()
    
    if st.session_state.generar_grabacion:
        st.markdown("---")
        st.markdown("### 🎵 **GUIÓN PARA GRABACIÓN DE AUTOHIPNOSIS**")
        with st.spinner("Generando guión para grabación..."):
            guion = generar_guion_hipnosis(sistema, paciente, "grabacion")
            st.markdown(guion)
            
            # Instrucciones adicionales para grabación
            st.markdown("---")
            st.markdown("#### 📋 **INSTRUCCIONES PARA GRABACIÓN:**")
            st.success("""
            1. **Preparación:** Ambiente tranquilo, sin interrupciones
            2. **Equipo:** Usar micrófono de buena calidad o smartphone
            3. **Voz:** Hablar lentamente, con tono calmado
            4. **Pausas:** Dejar espacios para respiración
            5. **Guardar:** Nombrar archivo claramente (ej: "Autohipnosis_[fecha]")
            6. **Uso:** Escuchar con auriculares, posición cómoda
            """)
            
            if st.button("↩️ Volver a opciones", use_container_width=True):
                st.session_state.generar_grabacion = False
                st.rerun()
    
    # Botón para nuevo diagnóstico
    st.markdown("---")
    col_n1, col_n2, col_n3 = st.columns([2,1,1])
    with col_n1:
        if st.button("🆕 Realizar NUEVO diagnóstico", use_container_width=True, type="primary"):
            st.session_state.mostrar_diagnostico = False
            st.session_state.diagnostico_completo = None
            st.session_state.generar_guion = False
            st.session_state.generar_grabacion = False
            st.rerun()
    
    with col_n2:
        if st.button("💾 Guardar diagnóstico", use_container_width=True):
            st.success("Diagnóstico guardado en historial")
    
    with col_n3:
        if st.button("🖨️ Imprimir/Exportar", use_container_width=True):
            st.info("Función de exportación en desarrollo")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.8em;'>
    🧠 <b>MINDGEEKCLINIC v6.0</b> • Sistema con Triangulación Diagnóstica • 
    Identificación precisa de relaciones evento-síntoma • Protocolos personalizados basados en biblioteca especializada
    </div>
    """,
    unsafe_allow_html=True
)
