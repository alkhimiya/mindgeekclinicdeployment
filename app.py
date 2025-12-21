
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
# URL CORREGIDA CON TU USUARIO 'alkhimiya'
ZIP_URL = "https://github.com/alkhimiya/mindgeekclinic/raw/main/mindgeekclinic_db.zip"

# ================= DESCARGAR Y PREPARAR BASE =================
@st.cache_resource
def cargar_sistema_completo():
    """Descarga la base completa y carga el sistema."""
    
    with st.spinner("🚀 Iniciando MINDGEEKCLINIC..."):
        try:
            # 1. Descargar el ZIP desde GitHub
            st.info("📥 Descargando base de conocimiento completa...")
            response = requests.get(ZIP_URL, stream=True)
            
            if response.status_code != 200:
                st.error("❌ No se pudo descargar la base de datos. Verifica que el archivo ZIP exista en tu repositorio.")
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
                st.error("❌ El archivo ZIP está vacío o no se descomprimió correctamente.")
                return None
            
            st.success(f"✅ Base cargada: {len(archivos)} archivos de conocimiento")
            
            # 4. Cargar en LangChain/Chroma
            st.info("🧠 Inicializando sistema experto...")
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            vector_store = Chroma(persist_directory=extract_path, embedding_function=embeddings)
            
            # 5. Conectar a Gemini
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
            
            st.success("🎯 SISTEMA MINDGEEKCLINIC ACTIVO")
            st.caption(f"Base de conocimiento: {len(archivos)} archivos | Modelo: Gemini 1.5 Flash")
            return qa_chain
            
        except Exception as e:
            st.error(f"❌ Error crítico: {str(e)[:200]}")
            return None

# ================= INTERFAZ PRINCIPAL =================
st.set_page_config(
    page_title="MINDGEEKCLINIC",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS profesional
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 0;
    }
    .subtitle {
        text-align: center;
        color: #4B5563;
        font-size: 1.2rem;
        margin-top: 0;
    }
    .info-box {
        background: #F0F9FF;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #3B82F6;
        margin: 10px 0;
    }
    .chat-container {
        max-width: 900px;
        margin: 0 auto;
    }
</style>
""", unsafe_allow_html=True)

# HEADER
st.markdown('<h1 class="main-header">🧠 MINDGEEKCLINIC</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Sistema de Asistencia Clínica Especializada | Para uso profesional</p>', unsafe_allow_html=True)
st.markdown("---")

# SIDEBAR
with st.sidebar:
    st.title("⚙️ Configuración")
    
    st.markdown("### 📚 Base de Conocimiento")
    st.markdown("""
    **Biblioteca completa del Dr. González:**
    - 70 libros profesionales
    - Biodescodificación
    - Hipnosis Clínica
    - Psicología
    """)
    
    st.markdown("### 🔍 Sistema")
    st.markdown("""
    - 🤖 **IA:** Google Gemini 1.5 Flash
    - 🔗 **Arquitectura:** RAG especializado
    - 📊 **Búsqueda:** 6 fragmentos más relevantes
    """)
    
    if st.button("🔄 Reiniciar Sistema", type="secondary", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()

# CARGA DEL SISTEMA
sistema = cargar_sistema_completo()

# ÁREA DE CHAT
if sistema:
    st.markdown('<div class="info-box">✅ <strong>Sistema activo con toda la base de conocimiento.</strong> Puede realizar su consulta clínica profesional.</div>', unsafe_allow_html=True)
    
    # Inicializar historial
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant",
            "content": "**MINDGEEKCLINIC activo.**\n\nHe cargado toda la biblioteca especializada del Dr. González. Estoy listo para analizar su consulta clínica con el conocimiento completo disponible."
        })
    
    # Contenedor de chat
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Mostrar historial
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Input del usuario
    if pregunta := st.chat_input("Escriba su consulta clínica profesional aquí..."):
        # Añadir pregunta
        st.session_state.messages.append({"role": "user", "content": pregunta})
        with st.chat_message("user"):
            st.markdown(f"**Consulta:** {pregunta}")
        
        # Generar respuesta
        with st.chat_message("assistant"):
            with st.spinner("🔍 Buscando en biblioteca especializada..."):
                try:
                    # Prompt clínico profesional
                    prompt_clinico = f"""Eres MINDGEEKCLINIC, el sistema de asistencia clínica del Dr. Luis Ernesto González.

INSTRUCCIONES:
1. Basa tu respuesta ÚNICA Y EXCLUSIVAMENTE en la biblioteca completa de 70 libros.
2. El tono debe ser TÉCNICO, PROFESIONAL y PRECISO.
3. Si la información no está en la biblioteca, indica claramente: "No hay información suficiente en la biblioteca para esta consulta específica."
4. Enfatiza la fundamentación clínica.

CONSULTA PROFESIONAL: {pregunta}

ANÁLISIS Y RESPUESTA CLÍNICA:"""
                    
                    respuesta = sistema.invoke({"query": prompt_clinico})
                    texto_respuesta = respuesta['result']
                    
                    # Mostrar respuesta
                    st.markdown(texto_respuesta)
                    
                    # Mostrar fuentes si están disponibles
                    if respuesta.get('source_documents'):
                        fuentes = []
                        for doc in respuesta['source_documents'][:3]:
                            fuente = doc.metadata.get('source', 'Documento')
                            if fuente not in fuentes:
                                fuentes.append(fuente)
                        
                        if fuentes:
                            st.markdown("---")
                            st.caption(f"**📖 Referencias consultadas:** {', '.join(fuentes)}")
                    
                    # Guardar en historial
                    st.session_state.messages.append({
                        "role": "
