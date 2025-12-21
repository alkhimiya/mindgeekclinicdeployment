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

# ================= CONFIGURACIÓN CORREGIDA =================
# 1. API Key (SOLO desde Secrets de Streamlit Cloud)
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")

# 2. URL EXACTA y CORREGIDA de tu archivo ZIP (¡CONFIRMADA POR TI!)
ZIP_URL = "https://github.com/alkhimiya/mindgeekclinicdeployment/raw/refs/heads/main/mindgeekclinic_db.zip"

# ================= FUNCIÓN PRINCIPAL =================
@st.cache_resource
def cargar_sistema_completo():
    """Descarga la base desde GitHub y carga el sistema."""
    
    # VERIFICACIÓN INMEDIATA: Si no hay API Key, detener todo.
    if not GEMINI_API_KEY:
        st.error("❌ ERROR: La API Key de Gemini (GEMINI_API_KEY) no está configurada en Streamlit Cloud Secrets.")
        st.info("Ve a Settings > Secrets y añade: GEMINI_API_KEY = 'tu_clave_aqui'")
        return None
    
    with st.spinner("🚀 Iniciando MINDGEEKCLINIC..."):
        try:
            # 1. Descargar el ZIP desde la URL CORRECTA
            st.info(f"📥 Descargando base de conocimiento desde GitHub...")
            response = requests.get(ZIP_URL, stream=True, timeout=60)
            
            # VERIFICACIÓN CRÍTICA DEL ERROR 404
            if response.status_code == 404:
                st.error(f"❌ ERROR 404: No se encuentra el archivo en la URL.")
                st.info(f"URL usada: {ZIP_URL}")
                st.info("Verifica que el archivo 'mindgeekclinic_db.zip' esté en tu repositorio 'mindgeekclinicdeployment'.")
                return None
            elif response.status_code != 200:
                st.error(f"❌ Error HTTP {response.status_code} al descargar.")
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
                st.error("❌ El archivo ZIP se descargó pero está vacío o no se pudo descomprimir.")
                return None
            
            st.success(f"✅ Base de conocimiento cargada: {len(archivos)} archivos procesados.")
            
            # 4. Cargar en LangChain/Chroma
            st.info("🧠 Inicializando motor de búsqueda especializado...")
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            vector_store = Chroma(persist_directory=extract_path, embedding_function=embeddings)
            
            # 5. Conectar a Gemini
            st.info("🔌 Conectando con IA Gemini...")
            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=GEMINI_API_KEY,
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
            
            st.success("🎯 ¡SISTEMA MINDGEEKCLINIC ACTIVO Y LISTO!")
            return qa_chain
            
        except requests.exceptions.Timeout:
            st.error("❌ Tiempo de espera agotado. El archivo ZIP es muy grande o hay problemas de red.")
            return None
        except Exception as e:
            st.error(f"❌ Error inesperado: {str(e)[:150]}")
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
    st.markdown("### ⚙️ Configuración")
    if st.button("🔄 Reiniciar Sistema", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()

# CARGA DEL SISTEMA
sistema = cargar_sistema_completo()

# ÁREA DE CHAT
if sistema:
    st.success("✅ **Sistema activo.** Puede realizar su consulta clínica profesional.")
    
    # Inicializar historial
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant",
            "content": "MINDGEEKCLINIC listo. Soy su asistente especializado. ¿En qué puedo asistirle?"
        })
    
    # Mostrar historial
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Input del usuario
    if pregunta := st.chat_input("Escriba su consulta clínica aquí..."):
        st.session_state.messages.append({"role": "user", "content": pregunta})
        with st.chat_message("user"):
            st.markdown(pregunta)
        
        with st.chat_message("assistant"):
            with st.spinner("🔍 Buscando en biblioteca especializada..."):
                try:
                    # Prompt profesional simplificado
                    prompt = f"Eres MINDGEEKCLINIC. Responde de manera técnica y profesional basándote en la biblioteca disponible. Consulta: {pregunta}"
                    respuesta = sistema.invoke({"query": prompt})
                    st.markdown(respuesta['result'])
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": respuesta['result']
                    })
                except Exception as e:
                    st.error(f"Error al procesar: {e}")

else:
    # Mensaje de error genérico (los errores específicos ya se mostraron arriba)
    st.warning("⚠️ El sistema no está disponible. Revisa los mensajes de error en la parte superior de la página.")
