#!/usr/bin/env python3
"""
DIAGNÓSTICO FINAL - Captura error REAL de streamlit_app.py
"""
import os
import sys
import subprocess

print("🔍 DIAGNÓSTICO: Ejecutando streamlit_app.py...")
sys.stdout.flush()

# Intentar ejecutar streamlit_app.py DIRECTAMENTE como módulo Python
# Esto nos dará el error REAL antes de que Streamlit lo oculte
try:
    print("📝 Probando importación directa...")
    
    # Primero verificar si el archivo tiene errores de sintaxis
    resultado = subprocess.run(
        [sys.executable, "-m", "py_compile", "streamlit_app.py"],
        capture_output=True,
        text=True
    )
    
    if resultado.returncode != 0:
        print("❌ ERROR DE SINTAXIS en streamlit_app.py:")
        print(resultado.stderr)
        sys.exit(1)
    
    print("✅ Sintaxis OK. Probando importación...")
    
    # Ahora intentar importarlo para ver errores de import/ejecución
    import importlib.util
    spec = importlib.util.spec_from_file_location("streamlit_app", "streamlit_app.py")
    module = importlib.util.module_from_spec(spec)
    
    # Capturar cualquier error durante la importación/ejecución
    try:
        spec.loader.exec_module(module)
        print("✅ Importación/ejecución inicial OK")
    except Exception as e:
        print(f"❌ ERROR durante importación/ejecución: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
except Exception as e:
    print(f"💥 Error en diagnóstico: {e}")
    import traceback
    traceback.print_exc()

# Si llegamos aquí, intentar ejecutar Streamlit normalmente
print("\n🚀 Iniciando Streamlit normalmente...")
sys.stdout.flush()

os.system("streamlit run streamlit_app.py --server.address 0.0.0.0")
