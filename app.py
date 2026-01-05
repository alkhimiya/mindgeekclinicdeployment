#!/usr/bin/env python3
"""
Punto de entrada INTELIGENTE para Streamlit Cloud.
Espera si el puerto está ocupado y reintenta.
"""
import os
import sys
import time
import subprocess

def puerto_disponible(puerto):
    """Verifica si un puerto está disponible"""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            s.bind(('0.0.0.0', puerto))
            return True
    except:
        return False

def main():
    print("🚀 MindGeek Clinic - Iniciando con lógica de reintento...")
    
    # Configuración
    puerto = 8501
    max_intentos = 5
    espera_entre_intentos = 3  # segundos
    
    # Verificar si streamlit_app.py existe
    if not os.path.exists("streamlit_app.py"):
        print("❌ ERROR: No se encuentra streamlit_app.py")
        sys.exit(1)
    
    # Intentar hasta que el puerto esté disponible
    for intento in range(max_intentos):
        print(f"📡 Intento {intento + 1}/{max_intentos} en puerto {puerto}...")
        
        if puerto_disponible(puerto):
            print(f"✅ Puerto {puerto} disponible. Iniciando Streamlit...")
            # Ejecutar Streamlit y SALIR del script
            os.execvp("streamlit", [
                "streamlit", "run", "streamlit_app.py",
                "--server.port", str(puerto),
                "--server.address", "0.0.0.0",
                "--server.headless", "true"
            ])
        else:
            print(f"⏳ Puerto {puerto} ocupado. Esperando {espera_entre_intentos}s...")
            time.sleep(espera_entre_intentos)
    
    print(f"❌ No se pudo obtener el puerto {puerto} después de {max_intentos} intentos")
    print("💡 Streamlit Cloud puede tener un conflicto interno.")
    print("🔄 Intentando puerto alternativo 8502 como último recurso...")
    
    # Último intento con puerto diferente
    os.execvp("streamlit", [
        "streamlit", "run", "streamlit_app.py",
        "--server.port", "8502",
        "--server.address", "0.0.0.0",
        "--server.headless", "true"
    ])

if __name__ == "__main__":
    main()
