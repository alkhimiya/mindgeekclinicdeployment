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

GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
ZIP_URL = "https://github.com/alkhimiya/mindgeekclinicdeployment/raw/refs/heads/main/mindgeekclinic_db.zip"

@st.cache_resource
def cargar_sistema_completo():
    if not GEMINI_API_KEY:
        st.error("❌ ERROR: Configura GEMINI_API_KEY en Streamlit Cloud Secrets.")
        return None
    
    with st.spinner("🚀 Iniciando MINDGEEKCLINIC..."):
        try:
            st.info("📥 Descargando base de conocimiento...")
            response = requests.get(ZIP_URL, stream=True, timeout=60)
            if response.status_code != 200:
                st.error(f"❌ Error {response.status_code} al descargar.")
                return None
            
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "database.zip")
            extract_path = os.path.join(temp_dir, "mindgeekclinic_db")
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            st.info("🗜️ Descomprimiendo...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            
            archivos = [f for f in Path(extract_path).rglob('*') if f.is_file()]
            if len(archivos) == 0:
                st.error("❌ El ZIP está vacío.")
                return None
            
            st.success(f"✅ Base cargada: {len(archivos)} archivos.")
            
            st.info("🧠 Inicializando motor de búsqueda...")
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            vector_store = Chroma(persist_directory=extract_path, embedding_function=embeddings)
            
            st.info("🔌 Conectando con IA Gemini...")
            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash-latest",  # OPCIÓN 1
                google_api_key=GEMINI_API_KEY,
                temperature=0.3,
                max_tokens=2000
            )
            
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=vector_store.as_retriever(search_kwargs={"k": 6}),
                return_source_documents=True
            )
            
            st.success("🎯 ¡SISTEMA MINDGEEKCLINIC ACTIVO!")
            return qa_chain
            
        except Exception as e:
            st.error(f"❌ Error crítico: {str(e)[:150]}")
            return None

st.set_page_config(page_title="MINDGEEKCLINIC", page_icon="🧠", layout="wide")
st.title("🧠 MINDGEEKCLINIC")
st.markdown("**Sistema de Asistencia Clínica Especializada**")
st.markdown("---")

with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    if st.button("🔄 Reiniciar Sistema", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()

sistema = cargar_sistema_completo()

if sistema:
    st.success("✅ **Sistema activo.** Puede realizar su consulta.")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant",
            "content": "MINDGEEKCLINIC listo. Soy su asistente especializado. ¿En qué puedo asistirle?"
        })
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    if pregunta := st.chat_input("Escriba su consulta clínica aquí..."):
        st.session_state.messages.append({"role": "user", "content": pregunta})
        with st.chat_message("user"):
            st.markdown(pregunta)
        
        with st.chat_message("assistant"):
            with st.spinner("🔍 Buscando en biblioteca..."):
                try:
                    prompt = f"Eres MINDGEEKCLINIC. Responde de manera técnica y profesional basándote en la biblioteca disponible. Consulta: {pregunta}"
                    respuesta = sistema.invoke({"query": prompt})
                    st.markdown(respuesta['result'])
                    st.session_state.messages.append({"role": "assistant", "content": respuesta['result']})
                except Exception as e:
                    st.error(f"Error: {e}")
else:
    st.warning("⚠️ El sistema no está disponible.")
