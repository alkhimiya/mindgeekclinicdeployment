import streamlit as st
import os
import zipfile
import tempfile
from pathlib import Path
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.chains import RetrievalQA
import requests

# ================= CONFIGURACIÓN INFALIBLE =================
# Intenta obtener la API Key de TRES maneras diferentes, en orden de prioridad
GEMINI_API_KEY = None

# 1. Primero, de los Secrets de Streamlit Cloud (LA FORMA CORRECTA)
if st.secrets.has_key("GEMINI_API_KEY"):
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    st.success("✅ API Key detectada desde Streamlit Secrets")
# 2. Si no, de una variable de entorno (para desarrollo local)
elif "GEMINI_API_KEY" in os.environ:
    GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
    st.info("ℹ️ API Key detectada desde variable de entorno")
# 3. Si no hay nada, MUESTRA ERROR CLARO
else:
    st.error("""
    ❌ ERROR CRÍTICO: No se encontró la API Key de Gemini.
    
    Por favor, configura tu clave en Streamlit Cloud:
    1. Ve a 'Settings' > 'Secrets'
    2. Añade esta línea:
       GEMINI_API_KEY = "AIzaSyTuClaveRealAqui123"
    3. Reinicia la aplicación.
    """)

# URL de tu base de datos (CORRECTA con tu usuario)
ZIP_URL = "https://github.com/alkhimiya/mindgeekclinic/raw/main/mindgeekclinic_db.zip"

# ================= FUNCIÓN PRINCIPAL (SOLO si hay API Key) =================
@st.cache_resource
def cargar_sistema_completo():
    """Descarga la base completa y carga el sistema."""
    
    # VERIFICACIÓN INMEDIATA: Si no hay API Key, detener todo aquí
    if not GEMINI_API_KEY:
        st.error("❌ El sistema no puede iniciar sin la API Key de Gemini.")
        return None
    
    with st.spinner("🚀 Iniciando MINDGEEKCLINIC..."):
        try:
            # 1. Descargar el ZIP desde GitHub
            st.info("📥 Descargando base de conocimiento completa...")
            response = requests.get(ZIP_URL, stream=True)
            
            if response.status_code != 200:
                st.error(f"❌ Error al descargar. Código: {response.status_code}")
                st.info(f"Verifica que este enlace funcione: {ZIP_URL}")
                return None
            
            # 2. Crear directorio temporal
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "database.zip")
            extract_path = os.path.join(temp_dir, "mindgeekclinic_db")
            
            # Guardar ZIP
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # 3. Descomprimir
            st.info("🗜️ Descomprimiendo conocimiento especializado...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            
            # Verificar contenido
            archivos = list(Path(extract_path).rglob('*'))
            archivos = [f for f in archivos if f.is_file()]
            
            if len(archivos) == 0:
                st.error("❌ El ZIP está vacío o no se descomprimió.")
                return None
            
            st.success(f"✅ Base cargada: {len(archivos)} archivos")
            
            # 4. Cargar en LangChain/Chroma
            st.info("🧠 Inicializando sistema experto...")
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            vector_store = Chroma(persist_directory=extract_path, embedding_function=embeddings)
            
            # 5. Conectar a Gemini (¡CON LA API Key VERIFICADA!)
            st.info("🔌 Conectando con Gemini...")
            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=GEMINI_API_KEY,  # ¡Aquí se usa la clave verificada!
                temperature=0.3,
                max_tokens=2000
            )
            
            # 6. Crear sistema RAG
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=vector_store.as_retriever(search_kwargs={"k": 6}),
                return_source_documents=True
            )
            
            st.success("🎯 SISTEMA MINDGEEKCLINIC ACTIVO")
            return qa_chain
            
        except Exception as e:
            st.error(f"❌ Error crítico: {str(e)[:200]}")
            return None

# ================= INTERFAZ PRINCIPAL =================
st.set_page_config(
    page_title="MINDGEEKCLINIC",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 MINDGEEKCLINIC")
st.markdown("**Sistema de Asistencia Clínica Especializada**")
st.markdown("---")

# SIDEBAR
with st.sidebar:
    st.markdown("### 🔧 Configuración")
    if st.button("🔄 Reiniciar Sistema", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()

# CARGA DEL SISTEMA
sistema = cargar_sistema_completo()

# ÁREA DE CHAT
if sistema:
    st.success("✅ **Sistema activo.** Puede realizar su consulta clínica.")
    
    # Inicializar historial
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant",
            "content": "MINDGEEKCLINIC listo. ¿En qué puedo asistirle?"
        })
    
    # Mostrar historial
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Input del usuario
    if pregunta := st.chat_input("Escriba su consulta aquí..."):
        st.session_state.messages.append({"role": "user", "content": pregunta})
        with st.chat_message("user"):
            st.markdown(pregunta)
        
        with st.chat_message("assistant"):
            with st.spinner("Procesando..."):
                try:
                    respuesta = sistema.invoke({"query": pregunta})
                    st.markdown(respuesta['result'])
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": respuesta['result']
                    })
                except Exception as e:
                    st.error(f"Error: {e}")

else:
    st.warning("⚠️ El sistema no está disponible. Revisa los mensajes de error arriba.")
