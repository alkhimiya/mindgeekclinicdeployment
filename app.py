import streamlit as st
import os
import zipfile
import tempfile
from pathlib import Path
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_classic.chains import RetrievalQA
import requests

# ================= CONFIGURACIÓN GROQ (GRATIS) =================
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")

ZIP_URL = "https://github.com/alkhimiya/mindgeekclinicdeployment/raw/refs/heads/main/mindgeekclinic_db.zip"

# ================= SISTEMA PRINCIPAL =================
@st.cache_resource
def cargar_sistema_completo():
    """Descarga la base y carga el sistema RAG con Groq."""
    
    if not GROQ_API_KEY:
        st.error("""
        ❌ **ERROR: Configura GROQ_API_KEY en Streamlit Cloud Secrets.**
        
        **Pasos para obtenerla GRATIS:**
        1. **Regístrate en:** https://console.groq.com
        2. **Haz clic en** "API Keys" (en el menú lateral)
        3. **Haz clic en** "Create API Key"
        4. **Copia** la clave (comienza con `gsk_...`)
        5. **En Streamlit Cloud:** Settings > Secrets > Añade:
           ```
           GROQ_API_KEY = "tu_clave_groq"
           ```
        6. **Reinicia** esta app
        """)
        return None
    
    with st.spinner("🚀 Iniciando MINDGEEKCLINIC con Groq (GRATIS)..."):
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
            
            # 6. CONECTAR CON GROQ (¡GRATIS SIN TARJETA!)
            st.info("🔌 Conectando con Groq Cloud (Llama 3.1 70B - GRATIS)...")
            
            try:
                from langchain_groq import ChatGroq
                
                llm = ChatGroq(
                    groq_api_key=GROQ_API_KEY,
                    model_name="llama3-70b-8192",  # Modelo GRATUITO
                    temperature=0.3,
                    max_tokens=2000
                )
                st.success("✅ Conectado a Groq Cloud (30K tokens/min GRATIS)")
                
            except ImportError:
                st.error("""
                ❌ **Falta instalar langchain-groq**
                
                **Agrega a tu requirements.txt:**
                ```
                langchain-groq==0.1.0
                ```
                """)
                return None
            except Exception as e:
                st.error(f"❌ Error con Groq: {str(e)[:100]}")
                return None
            
            # 7. CREAR SISTEMA RAG
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=vector_store.as_retriever(search_kwargs={"k": 6}),
                return_source_documents=True
            )
            
            st.success("🎯 ¡SISTEMA MINDGEEKCLINIC ACTIVO CON GROQ (100% GRATIS)!")
            return qa_chain
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)[:150]}")
            return None

# ================= INTERFAZ =================
st.set_page_config(
    page_title="MINDGEEKCLINIC - Groq Gratis",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 MINDGEEKCLINIC")
st.markdown("**Sistema de Asistencia Clínica Especializada - Powered by Groq Cloud (GRATIS)**")
st.markdown("---")

# BARRA LATERAL
with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    
    # Instrucciones para Groq
    with st.expander("🔑 Cómo obtener API Key GRATIS", expanded=True):
        st.markdown("""
        1. **Regístrate en:** [console.groq.com](https://console.groq.com)
        2. **Haz clic en** "API Keys" (menú lateral)
        3. **Crea una nueva API Key**
        4. **Copia** la clave (comienza con `gsk_...`)
        5. **Configura en Secrets** de Streamlit
        6. **Reinicia** la app
        """)
    
    if st.button("🔄 Reiniciar Sistema", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()
    
    st.markdown("---")
    st.caption("⚡ Groq Cloud • 30K tokens/min GRATIS • Sin tarjeta")

# CARGAR SISTEMA
sistema = cargar_sistema_completo()

# CHAT
if sistema:
    st.success("""
    ✅ **Sistema activo con Groq Cloud (100% GRATIS)**
    
    **Especificaciones:**
    • **Modelo:** Llama 3.1 70B parámetros
    • **Límite:** 30,000 tokens por minuto
    • **Costo:** $0 (sin tarjeta requerida)
    """)
    
    # Historial
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant",
            "content": "**MINDGEEKCLINIC** - Asistente Clínico con Groq Cloud\n\nHola, soy su asistente especializado, funcionando con IA 100% gratuita. ¿En qué puedo ayudarle hoy?"
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
    st.warning("⚠️ El sistema no está disponible. Sigue las instrucciones en la barra lateral para configurar Groq.")

# ================= FOOTER =================
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("🧠 MINDGEEKCLINIC v4.0")
with col2:
    st.caption("⚡ Groq Cloud • Llama 3.1 70B")
with col3:
    st.caption("🔓 100% Gratuito • Sin tarjeta")
