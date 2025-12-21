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

# ================= CONFIGURACIÓN =================
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
ZIP_URL = "https://github.com/alkhimiya/mindgeekclinicdeployment/raw/refs/heads/main/mindgeekclinic_db.zip"

# ================= SISTEMA PRINCIPAL =================
@st.cache_resource
def cargar_sistema_completo():
    """Descarga la base y carga el sistema RAG."""
    
    if not GEMINI_API_KEY:
        st.error("❌ ERROR: Configura GEMINI_API_KEY en Streamlit Cloud Secrets.")
        st.info("Settings > Secrets > Añade: GEMINI_API_KEY = 'tu_clave'")
        return None
    
    with st.spinner("🚀 Iniciando MINDGEEKCLINIC..."):
        try:
            # 1. DESCARGAR ZIP
            st.info("📥 Descargando base de conocimiento...")
            response = requests.get(ZIP_URL, stream=True, timeout=60)
            
            if response.status_code != 200:
                st.error(f"❌ Error {response.status_code}: No se pudo descargar el archivo.")
                st.info(f"Verifica que exista: {ZIP_URL}")
                return None
            
            # 2. PREPARAR DIRECTORIOS
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "database.zip")
            extract_path = os.path.join(temp_dir, "mindgeekclinic_db")
            
            # Guardar ZIP
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # 3. DESCOMPRIMIR
            st.info("🗜️ Descomprimiendo conocimiento...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            
            # 4. VERIFICAR CONTENIDO
            archivos = [f for f in Path(extract_path).rglob('*') if f.is_file()]
            if len(archivos) == 0:
                st.error("❌ El archivo ZIP está vacío o no se descomprimió.")
                return None
            
            st.success(f"✅ Base cargada: {len(archivos)} archivos procesados.")
            
            # 5. CARGAR BASE VECTORIAL
            st.info("🧠 Inicializando motor de búsqueda...")
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            vector_store = Chroma(persist_directory=extract_path, embedding_function=embeddings)
            
            # 6. CONECTAR GEMINI (OPCIÓN 2: models/gemini-1.5-flash)
            st.info("🔌 Conectando con IA Gemini...")
            llm = ChatGoogleGenerativeAI(
                model="models/gemini-1.5-flash",  # OPCIÓN 2 CON PREFIJO
                google_api_key=GEMINI_API_KEY,
                temperature=0.3,
                max_tokens=2000
            )
            
            # 7. CREAR SISTEMA RAG
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=vector_store.as_retriever(search_kwargs={"k": 6}),
                return_source_documents=True
            )
            
            st.success("🎯 ¡SISTEMA MINDGEEKCLINIC ACTIVO Y LISTO!")
            return qa_chain
            
        except Exception as e:
            st.error(f"❌ Error inesperado: {str(e)[:150]}")
            return None

# ================= INTERFAZ =================
st.set_page_config(
    page_title="MINDGEEKCLINIC",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 MINDGEEKCLINIC")
st.markdown("**Sistema de Asistencia Clínica Especializada**")
st.markdown("---")

# BARRA LATERAL
with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    if st.button("🔄 Reiniciar Sistema", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()

# CARGAR SISTEMA
sistema = cargar_sistema_completo()

# CHAT
if sistema:
    st.success("✅ **Sistema activo.** Puede realizar su consulta clínica.")
    
    # Historial
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
                    st.error(f"Error: {str(e)[:100]}")

else:
    st.warning("⚠️ El sistema no está disponible. Revisa los mensajes de error arriba.")
