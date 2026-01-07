#!/usr/bin/env python3
"""
Script para generar archivos de configuración para dispositivos Fanvil
"""

import os
import sys
import argparse
from string import Template

def create_config_file(mac_address, sip_username, sip_password, sip_server, output_dir):
    """
    Genera un archivo de configuración para un dispositivo Fanvil específico
    """
    
    # Plantilla de configuración
    config_template = Template("""# Configuracion para dispositivo Fanvil con MAC: $mac_address
# Generado automaticamente

# Configuracion SIP
account.1.enable = 1
account.1.label = "Cuenta SIP"
account.1.username = "$sip_username"
account.1.password = "$sip_password"
account.1.authid = "$sip_username"
account.1.display_name = "Usuario $sip_username"
account.1.sip_server.1.address = "$sip_server"
account.1.sip_server.1.port = 5060
account.1.sip_server.1.transport = 2
account.1.outbound_proxy.1.address = ""
account.1.outbound_proxy.1.port = 5060

# Configuracion de red
network.lan.ip_address = 0.0.0.0
network.lan.subnet_mask = 0.0.0.0
network.lan.gateway = 0.0.0.0
network.lan.dns_mode = 1
network.lan.primary_dns = 8.8.8.8
network.lan.secondary_dns = 8.8.4.4
network.lan.dhcp_mode = 1

# Configuracion de autoprovisionamiento
auto_provision.server = "http://tu-servidor.com/"
auto_provision.username = ""
auto_provision.password = ""
auto_provision.repeat.enable = 1
auto_provision.repeat.minutes = 1440
auto_provision.mode = 2

# Configuracion de funciones basicas
features.call_waiting.enable = 1
features.call_waiting.tone = 1
features.call_forward.always.dest = ""
features.call_forward.always.enable = 0
features.call_transfer.mode = 1
features.dtmf.relay_method = 1
features.dtmf.duration = 200
features.dtmf.volume = 5
features.ring_tone = 1

# Configuracion de audio
audio.handset.codec.1 = 110
audio.handset.codec.2 = 9
audio.handset.codec.3 = 0
audio.handset.codec.4 = 8
audio.handset.codec.5 = 102
audio.handset.vad = 1
audio.handset.cng = 1
audio.speaker.codec.1 = 110
audio.speaker.codec.2 = 9
audio.speaker.codec.3 = 0
audio.speaker.codec.4 = 8
audio.speaker.codec.5 = 102
audio.speaker.vad = 1
audio.speaker.cng = 1
audio.headset.codec.1 = 110
audio.headset.codec.2 = 9
audio.headset.codec.3 = 0
audio.headset.codec.4 = 8
audio.headset.codec.5 = 102
audio.headset.vad = 1
audio.headset.cng = 1

# Configuracion de seguridad
security.sip_tls.enable = 0
security.sip_tls.port = 5061
security.sip_tls.server_cert_verify = 1
security.http_tls.enable = 0
security.http_tls.port = 443
""")
    
    # Crear el contenido del archivo de configuración
    config_content = config_template.substitute(
        mac_address=mac_address,
        sip_username=sip_username,
        sip_password=sip_password,
        sip_server=sip_server
    )
    
    # Nombre del archivo basado en la dirección MAC
    filename = f"{mac_address.replace(':', '').replace('-', '').lower()}.cfg"
    filepath = os.path.join(output_dir, filename)
    
    # Escribir el archivo
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print(f"Archivo de configuración generado: {filepath}")
    return filepath

def main():
    parser = argparse.ArgumentParser(description='Generador de archivos de configuración para Fanvil')
    parser.add_argument('--mac', required=True, help='Dirección MAC del dispositivo')
    parser.add_argument('--username', required=True, help='Nombre de usuario SIP')
    parser.add_argument('--password', required=True, help='Contraseña SIP')
    parser.add_argument('--server', required=True, help='Servidor SIP')
    parser.add_argument('--output-dir', default='../config', help='Directorio de salida (por defecto: ../config)')
    
    args = parser.parse_args()
    
    # Asegurarse de que el directorio de salida exista
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Crear el archivo de configuración
    create_config_file(
        args.mac,
        args.username,
        args.password,
        args.server,
        args.output_dir
    )

if __name__ == "__main__":
    main()