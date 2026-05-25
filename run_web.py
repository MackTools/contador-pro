# run_web.py - Script para ejecutar la versión web
import os
import sys

def main():
    print("=" * 50)
    print("📊 Contaduría - Versión Web")
    print("=" * 50)
    print()
    print("Iniciando servidor web...")
    print()
    print("🌐 La aplicación estará disponible en:")
    print("   Local: http://localhost:8501")
    print("   Red:   http://192.168.x.x:8501")
    print()
    print("📌 Credenciales de prueba:")
    print("   Usuario: demo@contaduria.com")
    print("   Contraseña: admin123")
    print()
    print("Presiona Ctrl+C para detener el servidor")
    print("=" * 50)
    
    os.system(f"{sys.executable} -m streamlit run web_app.py --server.port 8501 --server.address 0.0.0.0")

if __name__ == "__main__":
    main()
