#!/usr/bin/env python3
"""
Servidor simple para autoprovisionamiento de dispositivos Fanvil
"""

import http.server
import socketserver
import os
import logging
from pathlib import Path

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/provision_server.log'),
        logging.StreamHandler()
    ]
)

class FanvilProvisionHandler(http.server.SimpleHTTPRequestHandler):
    """Handler personalizado para el aprovisionamiento de Fanvil"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="config", **kwargs)
    
    def log_message(self, format, *args):
        """Registra las solicitudes entrantes"""
        logging.info(f"{self.address_string()} - {format % args}")
        super().log_message(format, *args)
    
    def end_headers(self):
        """Agrega encabezados de seguridad"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

def main():
    """Función principal para iniciar el servidor de aprovisionamiento"""
    
    # Crear directorios necesarios si no existen
    os.makedirs('config', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs('firmware', exist_ok=True)
    
    # Puerto por defecto para el servidor de aprovisionamiento
    PORT = 8000
    
    # Directorio donde se sirven los archivos de configuración
    os.chdir('config')
    
    print(f"Iniciando servidor de aprovisionamiento Fanvil en el puerto {PORT}")
    print("Asegúrese de que los archivos de configuración estén en el directorio 'config'")
    print("Los dispositivos Fanvil deben apuntar a: http://<IP_SERVIDOR>:{PORT}/<MAC>.cfg")
    print("Presione Ctrl+C para detener el servidor")
    
    try:
        with socketserver.TCPServer(("", PORT), FanvilProvisionHandler) as httpd:
            logging.info(f"Servidor de aprovisionamiento iniciado en puerto {PORT}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido por el usuario")
        logging.info("Servidor de aprovisionamiento detenido")
    except Exception as e:
        logging.error(f"Error al iniciar el servidor: {e}")
        print(f"Error al iniciar el servidor: {e}")

if __name__ == "__main__":
    main()