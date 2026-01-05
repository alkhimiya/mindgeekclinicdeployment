#!/usr/bin/env python3
"""
PUNTO DE ENTRADA PURA STREAMLIT - Sin rastros de Flask
"""
import os
import sys

# 1. Verificar que streamlit_app.py existe
if not os.path.exists("streamlit_app.py"):
    print("❌ ERROR: streamlit_app.py no encontrado")
    sys.exit(1)

# 2. Obtener puerto (Streamlit Cloud lo maneja internamente)
port = os.environ.get("PORT", "8501")

# 3. Mensaje claro para logs
print(f"🚀 Iniciando MindGeek Clinic en puerto {port}")
sys.stdout.flush()

# 4. EJECUCIÓN PURA STREAMLIT - SIN FLASK
os.execlp(
    "streamlit", "streamlit", "run", "streamlit_app.py",
    "--server.port", port,
    "--server.address", "0.0.0.0",
    "--server.headless", "true"
)
