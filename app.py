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
import groq

# ================= CONFIGURACIÓN =================
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")
ZIP_URL = "https://github.com/alkhimiya/mindgeekclinicdeployment/raw/refs/heads/main/mindgeekclinic_db.zip"

# ================= DIAGNÓSTICO DE MODELOS =================
def detectar_modelos_disponibles():
    """Detecta automáticamente qué modelos están disponibles."""
    try:
        client = groq.Groq(api_key=GROQ_API_KEY)
        modelos = client.models.list()
        
        modelos_disponibles = []
        for modelo in modelos.data[:10]:  # Primeros 10 modelos
            modelos_disponibles.append(modelo.id)
        
        return modelos_disponibles
    except Exception as e:
        return []

# ================= SISTEMA PRINCIPAL =================
@st.cache_resource
def cargar_sistema_completo():
    """Descarga la base y carga el sistema RAG."""
    
    if not GROQ_API_KEY:
        st.error("❌ ERROR: Configura GROQ_API_KEY en Streamlit Cloud Secrets.")
        st.info("Settings > Secrets > Añade: GROQ_API_KEY = 'tu_clave_groq'")
        return None
    
    with st.spinner("🚀 Iniciando MINDGEEKCLINIC..."):
        try:
            # ===== PASO 1: DETECTAR MODELOS DISPONIBLES =====
            st.info("🔍 Detectando modelos disponibles en tu cuenta...")
            modelos = detectar_modelos_disponibles()
            
            if not modelos:
                st.error("❌ No se pudieron detectar modelos. Verifica tu API Key.")
                return None
            
            st.success(f"✅ {len(modelos)} modelos detectados")
            
            # Mostrar modelos disponibles
            with st.expander("📋 Modelos disponibles en tu cuenta"):
                for i, modelo in enumerate(modelos, 1):
                    st.write(f"{i}. `{modelo}`")
            
            # ===== PASO 2: BUSCAR MODELO QUE FUNCIONE =====
            modelos_a_probar = [
                "llama-3.3-70b-versatile",  # Más probable
                "llama-3.1-70b-versatile",
                "llama-3.2-90b-vision-preview",
                "llama-4-scout",
                "mixtral-8x7b-32768",
                "gemma2-9b-it",
                "llama-3.2-1b-preview",
            ]
            
            # Filtrar solo los que están en los disponibles
            modelos_validos = []
            for modelo in modelos_a_probar:
                for disponible in modelos:
                    if modelo in disponible or disponible in modelo:
                        modelos_validos.append(disponible)
            
            if not modelos_validos:
                st.error("❌ No se encontró ningún modelo compatible.")
                st.info("""
                **Instrucciones manuales:**
                1. Ve a: https://console.groq.com/playground
                2. Mira qué modelos ves en el dropdown
                3. Usa ese nombre EXACTO en el código
                """)
                return None
            
            st.info(f"🔌 Probando {len(modelos_validos)} modelos...")
            
            # ===== PASO 3: DESCARGAR BASE =====
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
            
            # ===== PASO 4: CARGAR EMBEDDINGS =====
            st.info("🧠 Inicializando motor de búsqueda...")
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            vector_store = Chroma(persist_directory=extract_path, embedding_function=embeddings)
            
            # ===== PASO 5: PROBAR MODELOS =====
            llm = None
            modelo_usado = None
            
            for modelo in modelos_validos:
                try:
                    st.write(f"  • Probando: `{modelo}`...")
                    llm = ChatGroq(
                        groq_api_key=GROQ_API_KEY,
                        model_name=modelo,
                        temperature=0.3,
                        max_tokens=2000
                    )
                    # Test rápido
                    test = llm.invoke("Hola")
                    modelo_usado = modelo
                    st.success(f"✅ Modelo funcionando: `{modelo}`")
                    break
                except Exception as e:
                    if "404" in str(e):
                        continue
                    else:
                        st.warning(f"  ✗ {modelo}: {str(e)[:50]}")
            
            if not llm:
                st.error("❌ Ningún modelo funcionó.")
                return None
            
            # ===== PASO 6: CREAR SISTEMA RAG =====
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=vector_store.as_retriever(search_kwargs={"k": 6}),
                return_source_documents=True
            )
            
            st.success(f"🎯 ¡SISTEMA ACTIVO! (Modelo: {modelo_usado})")
            return qa_chain
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)[:150]}")
            return None

# ================= INTERFAZ =================
st.set_page_config(
    page_title="MINDGEEKCLINIC - Diagnóstico",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 MINDGEEKCLINIC")
st.markdown("**Sistema con Diagnóstico Automático de Modelos**")
st.markdown("---")

# BARRA LATERAL
with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    
    # Instrucciones
    with st.expander("📋 Cómo ver modelos manualmente"):
        st.markdown("""
        1. **Ve a:** [console.groq.com/playground](https://console.groq.com/playground)
        2. **Haz clic** en el dropdown de modelos
        3. **Copia** el nombre EXACTO
        4. **Úsalo** en el código
        """)
    
    if st.button("🔄 Reiniciar Sistema", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()
    
    st.markdown("---")
    st.caption("🔍 Diagnóstico automático activado")

# CARGAR SISTEMA
sistema = cargar_sistema_completo()

# Resto del código de chat igual...
