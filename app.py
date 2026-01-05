#!/usr/bin/env python3
"""
ARCHIVO DE REDIRECCIÓN ÚNICO - Streamlit Cloud
Su sistema siempre ejecuta 'app.py'. Este archivo inicia tu aplicación real.
"""
import os
import sys

# Obtiene el puerto que asigna el entorno de la nube
port = os.environ.get('PORT', '8501')

# Comando directo y probado para lanzar tu aplicación Streamlit
streamlit_command = f"streamlit run streamlit_app.py --server.port {port} --server.address 0.0.0.0"
print(f"Iniciando aplicación: {streamlit_command}")
sys.stdout.flush()

# Ejecuta el comando. 'os.system' es simple y robusto para este caso.
os.execvp("streamlit", ["streamlit", "run", "streamlit_app.py", "--server.port", str(port), "--server.address", "0.0.0.0"])
