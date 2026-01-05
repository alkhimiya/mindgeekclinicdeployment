#!/usr/bin/env python3
"""
CONFIGURACIÓN DEFINITIVA - Streamlit Cloud
NO especificar puerto, dejar que Streamlit Cloud lo asigne
"""
import os
import sys

# Streamlit Cloud asignará automáticamente un puerto disponible
# NO uses --server.port, deja que Streamlit Cloud lo gestione
os.system("streamlit run streamlit_app.py --server.address=0.0.0.0")
