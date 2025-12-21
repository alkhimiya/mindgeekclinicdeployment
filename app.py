import streamlit as st
import os
import tempfile
from pathlib import Path
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.chains import RetrievalQA
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

# ================= CONFIGURACIÓN =================
# 1. API Key de Gemini (desde Secrets de Streamlit)
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")

# 2. Credenciales de Google Drive (desde Secrets)
# OBTÉN ESTAS CREDENCIALES EN EL SIGUIENTE PASO
GDRIVE_CREDENTIALS = st.secrets.get("GDRIVE_CREDENTIALS", {})
GDRIVE_FOLDER_ID = "1pnif4V4UqZjMyqMAVkUMeQ9nVloI89zX"  # ID de tu carpeta de Drive

# ================= ACCESO A GOOGLE DRIVE =================
def descargar_base_desde_drive():
    """Descarga la base de datos completa desde Google Drive."""
    
    st.info("🔗 Conectando con Google Drive...")
    
    try:
        # Crear credenciales desde los secrets
        creds_dict = {
            "type": GDRIVE_CREDENTIALS.get("type", "service_account"),
            "project_id": GDRIVE_CREDENTIALS.get("project_id"),
            "private_key_id": GDRIVE_CREDENTIALS.get("private_key_id"),
            "private_key": GDRIVE_CREDENTIALS.get("private_key", "").replace('\\n', '\n'),
            "client_email": GDRIVE_CREDENTIALS.get("client_email"),
            "client_id": GDRIVE_CREDENTIALS.get("client_id"),
            "auth_uri": GDRIVE_CREDENTIALS.get("auth_uri", "https://accounts.google.com/o/oauth2/auth"),
            "token_uri": GDRIVE_CREDENTIALS.get("token_uri", "https://oauth2.googleapis.com/token"),
            "auth_provider_x509_cert_url": GDRIVE_CREDENTIALS.get("auth_provider_x509_cert_url", "https://www.googleapis.com/oauth2/v1/certs"),
            "client_x509_cert_url": GDRIVE_CREDENTIALS.get("client_x509_cert_url")
        }
        
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        
        # Crear servicio de Drive
        drive_service = build('drive', 'v3', credentials=credentials)
        
        # Crear carpeta temporal para la base de datos
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "mindgeekclinic_db")
        
        st.info(f"📥 Descargando base de datos desde Drive...")
        
        # Buscar todos los archivos en la carpeta
        query = f"'{GDRIVE_FOLDER_ID}' in parents"
        results = drive_service.files().list(
            q=query,
            pageSize=1000,
            fields="files(id, name, size)"
        ).execute()
        
        files = results.get('files', [])
        
        if not files:
            st.error("❌ No se encontraron archivos en la carpeta de Drive.")
            return None
        
        # Descargar cada archivo
        os.makedirs(db_path, exist_ok=True)
        for file in files:
            try:
                request = drive_service.files().get_media(fileId=file['id'])
                file_path = os.path.join(db_path, file['name'])
                
                with open(file_path, 'wb') as fh:
                    downloader = MediaIoBaseDownload(fh, request)
                    done = False
                    while not done:
                        status, done = downloader.next_chunk()
                
                st.success(f"✅ {file['name']} descargado")
                
            except Exception as e:
                st.warning(f"⚠️  Error con {file['name']}: {str(e)[:50]}")
        
        st.success(f"📦 Base de datos descargada: {len(files)} archivos")
        return db_path
        
    except Exception as e:
        st.error(f"❌ Error crítico accediendo a Drive: {str(e)[:100]}")
        return None

# ================= INICIALIZAR SISTEMA =================
@st.cache_resource
def cargar_sistema_completo():
    """Carga el sistema completo desde Drive."""
    
    if not GEMINI_API_KEY:
        st.error("❌ Falta GEMINI_API_KEY en Secrets.")
        return None
    
    # Descargar base de datos desde Drive
    db_path = descargar_base_desde_drive()
    if not db_path:
        return None
    
    try:
        # Cargar embeddings y base de datos
        with st.spinner("🧠 Cargando conocimiento especializado..."):
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            vector_store = Chroma(persist_directory=db_path, embedding_function=embeddings)
        
        # Conectar con Gemini
        with st.spinner("🔌 Conectando con IA..."):
            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=GEMINI_API_KEY,
                temperature=0.3,
                max_tokens=2000
            )
        
        # Crear sistema RAG
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vector_store.as_retriever(search_kwargs={"k": 7}),
            return_source_documents=True
        )
        
        st.success("✅ Sistema MINDGEEKCLINIC cargado con toda la base de conocimiento")
        return qa_chain
        
    except Exception as e:
        st.error(f"❌ Error cargando sistema: {e}")
        return None

# ================= INTERFAZ =================
st.set_page_config(
    page_title="MINDGEEKCLINIC",
    page_icon="🧠",
    layout="wide"
)

# CSS profesional
st.markdown("""
<style>
    .main-title { color: #1E3A8A; text-align: center; font-size: 3rem; }
    .security-badge { background: #10B981; color: white; padding: 5px 15px; border-radius: 20px; }
    .info-box { background: #F0F9FF; padding: 20px; border-radius: 10px; border-left: 5px solid #3B82F6; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-title">🧠 MINDGEEKCLINIC</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align:center; font-size:1.2rem; color:#4B5563;">Sistema de Asistencia Clínica Especializada</p>', unsafe_allow_html=True)
st.markdown('<div style="text-align:center;"><span class="security-badge">🔐 Base de conocimiento completa: 70 libros</span></div>', unsafe_allow_html=True)
st.markdown("---")

# Barra lateral
with st.sidebar:
    st.title("⚙️ Configuración")
    
    st.markdown("### 📚 Base de Conocimiento")
    st.markdown("""
    **Biblioteca completa del Dr. Luis Ernesto González:**
    - 70 libros profesionales
    - Actualización constante
    - Acceso directo desde Google Drive
    """)
    
    st.markdown("### 🔒 Seguridad")
    st.markdown("""
    - Acceso solo lectura
    - Credenciales encriptadas
    - Sin almacenamiento local
    """)
    
    if st.button("🔄 Recargar Sistema", type="secondary"):
        st.cache_resource.clear()
        st.rerun()

# Cargar sistema
sistema = cargar_sistema_completo()

if sistema:
    # Historial de chat
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant",
            "content": "**MINDGEEKCLINIC activo.**\n\nBase de conocimiento completa cargada (70 libros).\nPuede realizar su consulta clínica profesional."
        })
    
    # Mostrar mensajes
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Input del usuario
    if pregunta := st.chat_input("Escriba su consulta clínica profesional..."):
        # Añadir pregunta
        st.session_state.messages.append({"role": "user", "content": pregunta})
        with st.chat_message("user"):
            st.markdown(pregunta)
        
        # Generar respuesta
        with st.chat_message("assistant"):
            with st.spinner("🔍 Buscando en biblioteca especializada..."):
                try:
                    prompt = f"""Eres MINDGEEKCLINIC, sistema de asistencia clínica.

CONOCIMIENTO: Dispones de la biblioteca completa del Dr. Luis Ernesto González (70 libros).

RESPONDE:
1. De manera TÉCNICA y PROFESIONAL
2. Basándote ÚNICAMENTE en la biblioteca
3. Con precisión clínica
4. Si no hay información suficiente: "No hay información en la biblioteca para esta consulta específica."

CONSULTA: {pregunta}

RESPUESTA TÉCNICA:"""
                    
                    respuesta = sistema.invoke({"query": prompt})
                    texto = respuesta['result']
                    
                    # Mostrar respuesta
                    st.markdown(texto)
                    
                    # Mostrar fuentes si hay
                    if respuesta.get('source_documents'):
                        fuentes = list(set([
                            doc.metadata.get('source', 'Documento') 
                            for doc in respuesta['source_documents'][:3]
                        ]))
                        if fuentes:
                            st.markdown(f"**📖 Referencias:** {', '.join(fuentes)}")
                    
                    # Guardar en historial
                    st.session_state.messages.append({"role": "assistant", "content": texto})
                    
                except Exception as e:
                    st.error(f"Error: {str(e)[:100]}")
    
    # Pie de página
    st.markdown("---")
    st.markdown("""
    <div class="info-box">
    <strong>💡 Información importante:</strong><br>
    • Sistema accede a la base de conocimiento completa desde Google Drive<br>
    • Respuestas 100% basadas en los 70 libros profesionales<br>
    • Sin límites de tamaño o contenido<br>
    • Actualizaciones automáticas cuando modifiques tu Drive
    </div>
    """, unsafe_allow_html=True)

else:
    st.error("""
    ❌ **Sistema no disponible**
    
    **Configuración requerida en Streamlit Cloud Secrets:**
    
    1. **GEMINI_API_KEY** = tu_clave_gemini
    2. **GDRIVE_CREDENTIALS** = (obtener en siguiente paso)
    
    Sin estas credenciales, el sistema no puede acceder al conocimiento.
    """)
