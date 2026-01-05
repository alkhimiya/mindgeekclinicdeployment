#!/usr/bin/env python3
"""
DIAGNÓSTICO DE ERRORES - Streamlit Cloud
Este archivo ejecuta streamlit_app.py y captura cualquier error
"""
import os
import sys
import subprocess

print("🔍 MINDGEEK CLINIC - Iniciando diagnóstico...")
print(f"📂 Directorio actual: {os.getcwd()}")
print(f"📄 Archivo principal: streamlit_app.py")

# Verificar que el archivo existe
if not os.path.exists("streamlit_app.py"):
    print("❌ ERROR CRÍTICO: No se encuentra streamlit_app.py")
    sys.exit(1)

print("✅ streamlit_app.py encontrado. Ejecutando...")

# Ejecutar Streamlit y capturar TODA la salida (incluidos errores)
try:
    # Usar subprocess para capturar stdout y stderr
    resultado = subprocess.run(
        ["streamlit", "run", "streamlit_app.py", "--server.port", "8501", "--server.address", "0.0.0.0"],
        capture_output=True,
        text=True,
        timeout=30  # Esperar 30 segundos máximo
    )
    
    print("\n" + "="*60)
    print("📤 SALIDA DE STREAMLIT (stdout):")
    print("="*60)
    print(resultado.stdout[-2000:] if resultado.stdout else "(vacío)")  # Últimos 2000 caracteres
    
    print("\n" + "="*60)
    print("❌ ERRORES DE STREAMLIT (stderr):")
    print("="*60)
    print(resultado.stderr[-2000:] if resultado.stderr else "(vacío)")
    
    print("\n" + "="*60)
    print(f"📊 Código de salida: {resultado.returncode}")
    
except subprocess.TimeoutExpired:
    print("⏰ Timeout: La aplicación tardó demasiado en iniciar")
except Exception as e:
    print(f"💥 Error ejecutando Streamlit: {e}")
