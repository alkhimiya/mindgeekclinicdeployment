import streamlit as st
import os
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.chains import RetrievalQA

# ================= CONFIGURACIÓN =================
# Configura tu API Key de Gemini en Streamlit Cloud (Secrets)
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
PERSIST_DIR = "./mindgeekclinic_db"  # Nombre de la carpeta de tu base de datos

# ================= INICIALIZAR EL SISTEMA =================
@st.cache_resource
def cargar_sistema():
    """Carga la base de datos y el modelo de IA."""
    try:
        if not GEMINI_API_KEY:
            st.error("❌ ERROR: No se encontró la API Key de Gemini.")
            st.info("Por favor, configura la variable 'GEMINI_API_KEY' en Streamlit Cloud Secrets.")
            return None
        
        # 1. Cargar la base de datos de conocimiento
        with st.spinner("Cargando base de conocimiento MINDGEEKCLINIC..."):
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            vector_store = Chroma(persist_directory=PERSIST_DIR, embedding_function=embeddings)
        
        # 2. Conectar con Google Gemini
        with st.spinner("Conectando con IA..."):
            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",  # Modelo gratuito y rápido
                google_api_key=GEMINI_API_KEY,
                temperature=0.3,      # Bajo = más preciso, Alto = más creativo
                max_tokens=1500       # Longitud máxima de respuesta
            )
        
        # 3. Crear el sistema RAG (que busca en la base y responde)
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vector_store.as_retriever(search_kwargs={"k": 4}),
            return_source_documents=False
        )
        
        return qa_chain
        
    except Exception as e:
        st.error(f"❌ Error crítico: {e}")
        return None

# ================= INTERFAZ DE LA APLICACIÓN WEB =================
st.set_page_config(
    page_title="MINDGEEKCLINIC",
    page_icon="🧠",
    layout="centered"
)

# Título principal
st.title("🧠 MINDGEEKCLINIC")
st.markdown("**Sistema de Asistencia Clínica Especializada**")
st.markdown("---")

# Cargar el sistema (esto se hace solo una vez)
sistema = cargar_sistema()

# Si el sistema se cargó bien, mostrar el chat
if sistema:
    # Inicializar el historial del chat
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Mensaje de bienvenida
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Sistema MINDGEEKCLINIC activo. Puede realizar su consulta clínica profesional."
        })
    
    # Mostrar todos los mensajes anteriores
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Esperar una nueva pregunta del usuario
    if pregunta := st.chat_input("Escriba su consulta clínica aquí..."):
        # Añadir la pregunta del usuario al historial
        st.session_state.messages.append({"role": "user", "content": pregunta})
        
        # Mostrar la pregunta del usuario
        with st.chat_message("user"):
            st.markdown(pregunta)
        
        # Generar la respuesta del sistema
        with st.chat_message("assistant"):
            with st.spinner("Procesando consulta..."):
                try:
                    # Crear el prompt profesional
                    prompt_final = f"""Eres MINDGEEKCLINIC, el sistema de asistencia clínica.
Responde de manera profesional y técnica, basándote únicamente en el conocimiento disponible.

Consulta: {pregunta}

Respuesta técnica:"""
                    
                    # Obtener respuesta del sistema
                    respuesta = sistema.invoke({"query": prompt_final})
                    texto_respuesta = respuesta['result']
                    
                    # Mostrar la respuesta
                    st.markdown(texto_respuesta)
                    
                    # Guardar la respuesta en el historial
                    st.session_state.messages.append({"role": "assistant", "content": texto_respuesta})
                    
                except Exception as e:
                    st.error(f"Error al generar respuesta: {e}")
    
    # Barra lateral con información
    with st.sidebar:
        st.header("ℹ️ Acerca de MINDGEEKCLINIC")
        st.markdown("""
        Sistema de asistencia clínica especializada basado en la biblioteca del **Dr. Luis Ernesto González**.
        
        - 📚 **Base:** 70 libros profesionales
        - 🎯 **Ámbito:** Psicología, Biodescodificación, Hipnosis Clínica
        - 🤖 **IA:** Google Gemini 1.5 Flash
        
        *Uso exclusivo para profesionales.*
        """)
        
        # Botón para limpiar la conversación
        if st.button("Limpiar conversación"):
            st.session_state.messages = [
                {"role": "assistant", "content": "Conversación reiniciada. Puede realizar su consulta."}
            ]
            st.rerun()

# Si el sistema NO se pudo cargar
else:
    st.warning("""
    ⚠️ El sistema no se pudo cargar completamente.
    
    **Causas comunes:**
    1. La API Key de Gemini no está configurada en Streamlit Cloud
    2. La base de datos no está en la carpeta 'mindgeekclinic_db'
    3. Problemas de conexión
    
    **Solución en Streamlit Cloud:**
    1. Ve a la configuración de tu app
    2. En 'Secrets', añade: `GEMINI_API_KEY = tu_clave_de_gemini`
    3. Reinicia la aplicación
    """)
