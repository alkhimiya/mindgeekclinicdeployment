import streamlit as st
import os
import zipfile
import tempfile
from pathlib import Path
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_classic.chains import RetrievalQA
import requests
import google.generativeai as genai

# ================= CONFIGURACIÓN GEMINI GRATIS =================
# OPCIÓN 1: Desde secrets
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")

# OPCIÓN 2: Input manual en sidebar
if not GEMINI_API_KEY:
    with st.sidebar:
        st.info("🔑 **API Key GRATIS necesaria**")
        api_input = st.text_input(
            "Pega tu API Key de Google AI Studio:",
            type="password",
            placeholder="AIzaSy... (obténla gratis abajo ⬇️)"
        )
        if api_input:
            GEMINI_API_KEY = api_input
            st.success("✅ Key guardada. Haz clic en 'Reiniciar'")

ZIP_URL = "https://github.com/alkhimiya/mindgeekclinicdeployment/raw/refs/heads/main/mindgeekclinic_db.zip"

# ================= VERIFICAR GEMINI GRATIS =================
def verificar_gemini_gratis(api_key):
    """Verifica si la API Key tiene acceso a Gemini GRATIS."""
    try:
        genai.configure(api_key=api_key)
        
        # Listar modelos disponibles
        modelos = list(genai.list_models())
        
        # Buscar modelos GRATIS
        modelos_gratis = []
        for modelo in modelos:
            nombre = modelo.name.lower()
            if "flash" in nombre:  # Gemini Flash es GRATIS
                modelos_gratis.append(modelo.name)
        
        if modelos_gratis:
            return True, modelos_gratis
        else:
            return False, []
            
    except Exception as e:
        return False, []

# ================= OBTENER LLM GRATIS =================
def obtener_gemini_gratis():
    """Obtiene Gemini Flash GRATIS."""
    
    if not GEMINI_API_KEY:
        return None, "❌ No hay API Key"
    
    # Verificar que la key funcione
    funciona, modelos = verificar_gemini_gratis(GEMINI_API_KEY)
    
    if not funciona:
        return None, "❌ API Key inválida o sin acceso a Gemini GRATIS"
    
    # Intentar diferentes versiones de Gemini Flash (GRATIS)
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        # Probar modelos GRATIS en orden
        modelos_a_probar = [
            "gemini-1.5-flash",        # Versión estable GRATIS
            "gemini-1.5-flash-latest", # Última versión GRATIS
            "models/gemini-1.5-flash", # Con prefijo
            "gemini-1.0-pro",          # Básico (puede ser gratis)
        ]
        
        for modelo in modelos_a_probar:
            try:
                llm = ChatGoogleGenerativeAI(
                    model=modelo,
                    google_api_key=GEMINI_API_KEY,
                    temperature=0.3,
                    max_tokens=2000,
                    timeout=30
                )
                # Test rápido
                test = llm.invoke("Hola")
                return llm, f"✅ Conectado a {modelo} (GRATIS)"
            except:
                continue
        
        return None, "❌ Ningún modelo Gemini GRATIS funcionó"
        
    except ImportError:
        return None, "❌ Instala: pip install langchain-google-genai"

# ================= SISTEMA PRINCIPAL =================
@st.cache_resource
def cargar_sistema_completo():
    """Carga el sistema RAG con Gemini GRATIS."""
    
    with st.spinner("🚀 Iniciando MINDGEEKCLINIC (Gemini GRATIS)..."):
        try:
            # 1. DESCARGAR BASE DE CONOCIMIENTO
            st.info("📥 Descargando base de conocimiento...")
            response = requests.get(ZIP_URL, stream=True, timeout=60)
            
            if response.status_code != 200:
                st.error(f"❌ Error {response.status_code} al descargar.")
                return None
            
            # 2. PREPARAR DIRECTORIOS
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "database.zip")
            extract_path = os.path.join(temp_dir, "mindgeekclinic_db")
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # 3. DESCOMPRIMIR
            st.info("🗜️ Descomprimiendo...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            
            # 4. VERIFICAR CONTENIDO
            archivos = [f for f in Path(extract_path).rglob('*') if f.is_file()]
            if len(archivos) == 0:
                st.error("❌ El ZIP está vacío.")
                return None
            
            st.success(f"✅ Base cargada: {len(archivos)} archivos.")
            
            # 5. CARGAR EMBEDDINGS
            st.info("🧠 Inicializando motor de búsqueda...")
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            vector_store = Chroma(persist_directory=extract_path, embedding_function=embeddings)
            
            # 6. OBTENER GEMINI GRATIS
            st.info("🔌 Conectando con Gemini GRATIS...")
            llm, mensaje = obtener_gemini_gratis()
            
            if not llm:
                st.error(f"""
                {mensaje}
                
                **📋 CÓMO OBTENER GEMINI GRATIS (SIN TARJETA):**
                
                1. **Ve a:** [Google AI Studio](https://aistudio.google.com/)
                2. **Inicia sesión** con tu cuenta Google
                3. **En el menú lateral** haz clic en "Get API Key"
                4. **Haz clic** en "Create API Key"
                5. **Copia** la clave (comienza con AIza...)
                6. **Pégala** en la barra lateral ⬅️
                
                **💰 ES 100% GRATIS:**
                • 60 requests por minuto
                • 1,000,000 tokens por día
                • Sin tarjeta de crédito
                • Sin facturación
                """)
                return None
            
            st.success(mensaje)
            
            # 7. CREAR SISTEMA RAG
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=vector_store.as_retriever(search_kwargs={"k": 6}),
                return_source_documents=True
            )
            
            st.success("🎯 ¡SISTEMA MINDGEEKCLINIC ACTIVO CON GEMINI GRATIS!")
            return qa_chain
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)[:150]}")
            return None

# ================= INTERFAZ =================
st.set_page_config(
    page_title="MINDGEEKCLINIC - Gemini GRATIS",
    page_icon="🧠",
    layout="wide"
)

# Título
st.title("🧠 MINDGEEKCLINIC")
st.markdown("**Sistema de Asistencia Clínica Especializada - Gemini 1.5 Flash GRATIS**")
st.markdown("---")

# ================= BARRA LATERAL CON INSTRUCCIONES =================
with st.sidebar:
    st.image("https://www.gstatic.com/aihub/images/favicon/favicon-96x96.png", width=80)
    st.markdown("### 🔑 Obtén Gemini GRATIS")
    
    # Instrucciones visuales
    with st.expander("📋 **PASO A PASO (Haz clic aquí)**", expanded=True):
        st.markdown("""
        **1. 🌐 Ve a:**  
           [Google AI Studio](https://aistudio.google.com/)
        
        **2. 👤 Inicia sesión** con Google
        
        **3. 🔑 Haz clic en** "Get API Key"
           (en menú lateral o arriba a la derecha)
        
        **4. 🆕 Haz clic en** "Create API Key"
        
        **5. 📋 Copia** la clave (ej: `AIzaSyD...`)
        
        **6. 📝 Pégala** abajo ⬇️
        """)
    
    st.markdown("---")
    
    # Input para API Key
    st.markdown("### 📝 Pega tu API Key aquí:")
    api_key_input = st.text_input(
        "Clave Gemini GRATIS:",
        type="password",
        value=GEMINI_API_KEY if GEMINI_API_KEY else "",
        placeholder="AIzaSy..."
    )
    
    if api_key_input and api_key_input != GEMINI_API_KEY:
        st.session_state.nueva_api_key = api_key_input
        st.success("✅ Nueva key guardada. Haz clic en Reiniciar ⬇️")
    
    st.markdown("---")
    
    # Botón de reinicio
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Reiniciar", use_container_width=True, type="primary"):
            st.cache_resource.clear()
            st.rerun()
    
    with col2:
        if st.button("🧪 Probar API", use_container_width=True):
            if GEMINI_API_KEY:
                try:
                    genai.configure(api_key=GEMINI_API_KEY)
                    modelos = list(genai.list_models())
                    st.success(f"✅ Key válida. {len(modelos)} modelos")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)[:50]}")
    
    st.markdown("---")
    st.caption("💡 Gemini 1.5 Flash es GRATIS sin tarjeta")

# Usar nueva API Key si se proporcionó
if st.session_state.get("nueva_api_key"):
    GEMINI_API_KEY = st.session_state.nueva_api_key

# ================= CARGAR SISTEMA =================
sistema = cargar_sistema_completo()

# ================= CHAT =================
if sistema:
    st.success("""
    ✅ **Sistema activo con Gemini 1.5 Flash GRATIS**
    
    **Límites GRATIS:**
    • 60 requests por minuto
    • 1,000,000 tokens por día
    • 100% sin costo
    """)
    
    # Historial
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant",
            "content": "**MINDGEEKCLINIC** - Asistente Clínico con Gemini GRATIS\n\nHola, soy su asistente especializado. ¿En qué puedo ayudarle hoy?"
        })
    
    # Mostrar historial
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Input usuario
    if pregunta := st.chat_input("Escriba su consulta clínica aquí..."):
        st.session_state.messages.append({"role": "user", "content": pregunta})
        with st.chat_message("user"):
            st.markdown(pregunta)
        
        # Generar respuesta
        with st.chat_message("assistant"):
            with st.spinner("🔍 Buscando en biblioteca..."):
                try:
                    prompt = f"""Eres MINDGEEKCLINIC. Responde de manera técnica y profesional basándote ÚNICAMENTE en la biblioteca disponible.

Consulta: {pregunta}

Respuesta:"""
                    
                    respuesta = sistema.invoke({"query": prompt})
                    st.markdown(respuesta['result'])
                    
                    # Fuentes
                    if respuesta.get('source_documents'):
                        fuentes = []
                        for doc in respuesta['source_documents'][:3]:
                            fuente = doc.metadata.get('source', 'Documento')
                            if fuente not in fuentes:
                                fuentes.append(fuente)
                        if fuentes:
                            st.caption(f"📖 **Referencias:** {', '.join(fuentes)}")
                    
                    # Guardar
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": respuesta['result']
                    })
                    
                except Exception as e:
                    if "quota" in str(e).lower():
                        st.error("""
                        ❌ **Límite GRATIS alcanzado**
                        
                        **Soluciones:**
                        1. Espera 24 horas (se renueva diario)
                        2. Usa otra cuenta Google para nueva API Key
                        3. Prueba mañana
                        """)
                    else:
                        st.error(f"Error: {str(e)[:100]}")

else:
    st.warning("""
    ⚠️ **Sistema no disponible**
    
    **Sigue las instrucciones en la barra lateral para:**
    1. Obtener API Key GRATIS de Google AI Studio
    2. Pegarla en el campo de texto
    3. Hacer clic en "Reiniciar"
    """)

# ================= FOOTER =================
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("🧠 MINDGEEKCLINIC v3.0")
with col2:
    st.caption("⚡ Gemini 1.5 Flash GRATIS")
with col3:
    st.caption("🔓 Sin tarjeta requerida")
