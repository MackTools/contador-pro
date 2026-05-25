# run_web.py - Script para ejecutar la aplicación web

import subprocess
import sys
import os

def main():
    """Ejecuta la aplicación Streamlit"""
    print("🚀 Iniciando Contaduría Web...")
    print("📱 La aplicación se abrirá en tu navegador")
    print("⚠️  Presiona Ctrl+C para detener el servidor\n")
    
    # Obtener la ruta del archivo web_app.py
    web_app_path = os.path.join(os.path.dirname(__file__), "web_app.py")
    
    # Ejecutar streamlit
    cmd = [sys.executable, "-m", "streamlit", "run", web_app_path, "--server.port=8501", "--server.address=localhost"]
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n👋 Servidor detenido")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Asegúrate de tener instalado streamlit:")
        print("   pip install streamlit")

if __name__ == "__main__":
    main()
