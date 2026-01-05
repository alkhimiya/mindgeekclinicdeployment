#!/usr/bin/env python3
"""
Punto de entrada para Streamlit Cloud.
Simplemente ejecuta la aplicación principal.
"""
import os
import sys

port = os.environ.get('PORT', '8502')
os.system(f"streamlit run streamlit_app.py --server.port {port} --server.address 0.0.0.0")
