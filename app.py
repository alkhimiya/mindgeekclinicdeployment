#!/usr/bin/env python3
"""
CONFIGURACIÓN DEFINITIVA - Ignora problemas de health check
"""
import os
import time

# Dar tiempo para que todo se inicialice
time.sleep(2)

# Configuración MÍNIMA que funciona
os.system("streamlit run streamlit_app.py --server.address=0.0.0.0 --server.port=8501")
