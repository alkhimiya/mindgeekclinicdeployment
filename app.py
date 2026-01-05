#!/usr/bin/env python3
"""
CONFIGURACIÓN PROBADA para Streamlit Cloud
"""
import os
import sys

# Streamlit Cloud maneja el puerto automáticamente
# NO uses 8501 explícitamente
os.system("streamlit run streamlit_app.py --server.address 0.0.0.0 --server.headless true")
