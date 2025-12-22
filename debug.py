# Archivo: debug.py
# Script para diagnóstico rápido del sistema

import streamlit as st
import os
import sys

st.set_page_config(page_title="Debug MG Clinic", layout="wide")

st.title("🔧 Debug MindGeekClinic")
st.markdown("---")

# 1. Verificar Python y Streamlit
st.header("1. Información del Sistema")
col1, col2 = st.columns(2)

with col1:
    st.write("**Python:**")
    st.code(f"Versión: {sys.version}")
    
with col2:
    st.write("**Streamlit:**")
    try:
        import streamlit as st_module
        st.code(f"Versión: {st_module.__version__}")
    except:
        st.error("No se puede importar streamlit")

# 2. Verificar secrets
st.header("2. Secrets Configurados")
secrets_keys = ["GROQ_API_KEY", "SMTP_SERVER", "SENDER_EMAIL", "SMTP_PORT", "SENDER_PASSWORD"]

for key in secrets_keys:
    try:
        value = st.secrets.get(key)
        if value:
            masked_value = "*" * 10 + str(value)[-4:] if len(str(value)) > 4 else "****"
            st.success(f"✅ **{key}**: `{masked_value}`")
        else:
            st.error(f"❌ **{key}**: NO CONFIGURADO")
    except:
        st.error(f"⚠️ **{key}**: Error al leer")

# 3. Verificar imports críticos
st.header("3. Imports Críticos")
imports_para_verificar = [
    ("langchain", "0.1.20"),
    ("langchain_community", "0.0.31"),
    ("langchain_groq", "0.1.3"),
    ("chromadb", "0.4.24"),
    ("sentence_transformers", "2.7.0"),
    ("requests", "2.31.0")
]

for package, version_esperada in imports_para_verificar:
    try:
        module = __import__(package.replace("-", "_"))
        version_actual = getattr(module, "__version__", "Desconocida")
        
        if version_actual == version_esperada or version_actual.startswith(version_esperada.split(".")[0]):
            st.success(f"✅ **{package}**: {version_actual}")
        else:
            st.warning(f"⚠️ **{package}**: {version_actual} (esperada: {version_esperada})")
            
    except ImportError as e:
        st.error(f"❌ **{package}**: No se puede importar - {e}")

# 4. Test de conexión
st.header("4. Test de Conexión Externa")

if st.button("🌐 Probar conexión a GitHub", key="test_github"):
    import requests
    try:
        response = requests.get("https://github.com/alkhimiya/mindgeekclinicdeployment", timeout=10)
        if response.status_code == 200:
            st.success("✅ GitHub accesible correctamente")
        else:
            st.warning(f"⚠️ GitHub responde con código: {response.status_code}")
    except Exception as e:
        st.error(f"❌ Error conectando a GitHub: {e}")

if st.button("🔗 Probar URL de base de conocimiento", key="test_zip"):
    import requests
    try:
        response = requests.head("https://github.com/alkhimiya/mindgeekclinicdeployment/raw/refs/heads/main/mindgeekclinic_db.zip", timeout=10)
        if response.status_code == 200:
            st.success("✅ Base de conocimiento accesible")
        else:
            st.error(f"❌ Error: Código {response.status_code}")
    except Exception as e:
        st.error(f"❌ Error: {e}")

# 5. Verificar estructura de archivos
st.header("5. Estructura de Archivos")
import os

archivos_necesarios = ["app.py", "requirements.txt", ".streamlit/secrets.toml"]

for archivo in archivos_necesarios:
    if os.path.exists(archivo):
        tamaño = os.path.getsize(archivo)
        st.success(f"✅ **{archivo}**: {tamaño} bytes")
    else:
        st.error(f"❌ **{archivo}**: NO ENCONTRADO")

st.markdown("---")
st.info("**Para usar:** Ejecuta `streamlit run debug.py`")
