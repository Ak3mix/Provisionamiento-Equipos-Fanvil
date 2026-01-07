#!/usr/bin/env python3
"""
Script para generar archivos de configuración XML para dispositivos Fanvil en lote
"""

import os
import csv
import json
import argparse
from string import Template
from pathlib import Path


def load_template(template_path):
    """Carga la plantilla XML desde un archivo"""
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()


def create_config_from_data(template, phone_data):
    """Crea un archivo de configuración XML reemplazando variables en la plantilla"""
    # Reemplazar variables de la plantilla primero
    config_content = template
    
    # Reemplazar variables de la plantilla
    for key, value in phone_data.items():
        if value is None:
            value = ""
        placeholder = f'{{$%s}}' % key
        config_content = config_content.replace(placeholder, str(value))
    
    # Procesar condicionales Smarty paso a paso
    
    # 1. Determinar si incluir la segunda cuenta
    if phone_data.get('account.2.user_id', '').strip():
        # La segunda cuenta tiene datos, dejarla tal cual después de haber reemplazado variables
        # Solo procesar los condicionales internos de la segunda cuenta
        
        # Procesar Enable_Reg condicional para la cuenta 2
        enable_reg_conditional_2 = "{if isset($account.2.password)}1{else}0{/if}"
        if enable_reg_conditional_2 in config_content:
            if phone_data.get('account.2.password', '').strip():
                config_content = config_content.replace(enable_reg_conditional_2, "1")
            else:
                config_content = config_content.replace(enable_reg_conditional_2, "0")
        
        # Procesar condicionales de transporte para la cuenta 2
        transport_mapping = {
            'udp': '0',
            'tcp': '1',
            'tls': '2',
            'dns srv': '1'  # DNS SRV no tiene un valor único, se puede usar TCP
        }
        
        for transport_key, transport_value in transport_mapping.items():
            transport_conditional = f"{{if $account.2.sip_transport == '{transport_key}'}}<Transport>{transport_value}</Transport>{{/if}}"
            if transport_conditional in config_content:
                if phone_data.get('account.2.sip_transport', '').lower() == transport_key:
                    config_content = config_content.replace(transport_conditional, f"<Transport>{transport_value}</Transport>")
                else:
                    config_content = config_content.replace(transport_conditional, "")
        
        # Procesar condicionales de DNS SRV para la cuenta 2
        dns_srv_conditional_2 = "{if $account.2.sip_transport == 'dns srv'}<DNS_SRV>1</DNS_SRV>{/if}"
        if dns_srv_conditional_2 in config_content:
            if phone_data.get('account.2.sip_transport', '').lower() == 'dns srv':
                config_content = config_content.replace(dns_srv_conditional_2, "<DNS_SRV>1</DNS_SRV>")
            else:
                config_content = config_content.replace(dns_srv_conditional_2, "")
        
        dns_srv_mode_conditional_2 = "{if $account.2.sip_transport == 'dns srv'}<DNS_Mode>1</DNS_Mode>{/if}"
        if dns_srv_mode_conditional_2 in config_content:
            if phone_data.get('account.2.sip_transport', '').lower() == 'dns srv':
                config_content = config_content.replace(dns_srv_mode_conditional_2, "<DNS_Mode>1</DNS_Mode>")
            else:
                config_content = config_content.replace(dns_srv_mode_conditional_2, "")
    else:
        # La segunda cuenta no tiene datos, eliminarla completamente del archivo
        start_marker = "<!-- Second account starts here -->"
        end_marker = "<!-- End of second account -->"
        
        start_pos = config_content.find(start_marker)
        end_pos = config_content.find(end_marker)
        
        if start_pos != -1 and end_pos != -1:
            # Incluir también el marcador de cierre en la eliminación
            end_pos += len(end_marker)
            config_content = config_content[:start_pos] + config_content[end_pos:]
    
    # 2. Procesar condicionales de transporte para la cuenta 1
    transport_mapping = {
        'udp': '0',
        'tcp': '1',
        'tls': '2',
        'dns srv': '1'  # DNS SRV no tiene un valor único, se puede usar TCP
    }
    
    for transport_key, transport_value in transport_mapping.items():
        transport_conditional = f"{{if $account.1.sip_transport == '{transport_key}'}}<Transport>{transport_value}</Transport>{{/if}}"
        if transport_conditional in config_content:
            if phone_data.get('account.1.sip_transport', '').lower() == transport_key:
                config_content = config_content.replace(transport_conditional, f"<Transport>{transport_value}</Transport>")
            else:
                config_content = config_content.replace(transport_conditional, "")
    
    # 3. Procesar condicionales de DNS SRV para la cuenta 1
    dns_srv_conditional_1 = "{if $account.1.sip_transport == 'dns srv'}<DNS_SRV>1</DNS_SRV>{/if}"
    if dns_srv_conditional_1 in config_content:
        if phone_data.get('account.1.sip_transport', '').lower() == 'dns srv':
            config_content = config_content.replace(dns_srv_conditional_1, "<DNS_SRV>1</DNS_SRV>")
        else:
            config_content = config_content.replace(dns_srv_conditional_1, "")
    
    dns_srv_mode_conditional_1 = "{if $account.1.sip_transport == 'dns srv'}<DNS_Mode>1</DNS_Mode>{/if}"
    if dns_srv_mode_conditional_1 in config_content:
        if phone_data.get('account.1.sip_transport', '').lower() == 'dns srv':
            config_content = config_content.replace(dns_srv_mode_conditional_1, "<DNS_Mode>1</DNS_Mode>")
        else:
            config_content = config_content.replace(dns_srv_mode_conditional_1, "")
    
    # 4. Procesar Enable_Reg condicional para la cuenta 1
    enable_reg_conditional_1 = "{if isset($account.1.password)}1{else}0{/if}"
    if enable_reg_conditional_1 in config_content:
        if phone_data.get('account.1.password', '').strip():
            config_content = config_content.replace(enable_reg_conditional_1, "1")
        else:
            config_content = config_content.replace(enable_reg_conditional_1, "0")
    
    # 5. Procesar condicionales comunes
    
    # Condición para fanvil_time_display
    while '{if isset($fanvil_time_display)}' in config_content:
        start_tag = '{if isset($fanvil_time_display)}'
        else_part = '{else}'
        end_tag = '{/if}'
        
        start_pos = config_content.find(start_tag)
        if start_pos != -1:
            # Encontrar la parte 'else' y el final
            else_pos = config_content.find(else_part, start_pos)
            end_pos = config_content.find(end_tag, start_pos) + len(end_tag)
            
            if else_pos != -1 and else_pos < end_pos:
                # Extraer las partes
                if_part_start = start_pos + len(start_tag)
                if_part_end = else_pos
                else_part_start = else_pos + len(else_part)
                else_part_end = end_pos - len(end_tag)
                
                if_content = config_content[if_part_start:if_part_end].strip()
                else_content = config_content[else_part_start:else_part_end].strip()
                
                # Determinar qué valor usar
                if phone_data.get('fanvil_time_display', '').strip():
                    replacement = if_content
                else:
                    replacement = else_content
                
                # Reemplazar el bloque condicional completo
                config_content = config_content[:start_pos] + replacement + config_content[end_pos:]
            else:
                # Sin parte else, solo eliminar la condición
                config_content = config_content.replace(start_tag, '').replace(end_tag, '')
    
    # 6. Reemplazar cualquier variable restante que no haya sido procesada
    remaining_vars = [
        'account.2.sip_port', 'account.2.register_expires', 'account.2.outbound_proxy_primary',
        'account.2.outbound_proxy_secondary', 'fanvil_time_display', 'fanvil_date_display',
        'http_auth_username', 'http_auth_password', 'domain_name', 'fanvil_server_name',
        'dns_server_primary', 'dns_server_secondary', 'ntp_server_primary', 'ntp_server_secondary',
        'fanvil_time_zone', 'fanvil_location', 'fanvil_time_zone_name', 'fanvil_enable_dst',
        'fanvil_greeting'
    ]
    
    for var in remaining_vars:
        placeholder = f'{{$%s}}' % var
        if placeholder in config_content:
            value = phone_data.get(var, '')
            if not value:
                # Asignar valor por defecto si no está definido
                defaults = {
                    'account.2.sip_port': '5060',
                    'account.2.register_expires': '3600',
                    'account.2.outbound_proxy_primary': '',
                    'account.2.outbound_proxy_secondary': '',
                    'fanvil_time_display': '0',
                    'fanvil_date_display': '0',
                    'http_auth_username': '',
                    'http_auth_password': '',
                    'domain_name': 'example.com',
                    'fanvil_server_name': phone_data.get('account.1.server_address', 'sip.example.com'),
                    'dns_server_primary': '8.8.8.8',
                    'dns_server_secondary': '8.8.4.4',
                    'ntp_server_primary': 'pool.ntp.org',
                    'ntp_server_secondary': 'time.nist.gov',
                    'fanvil_time_zone': 'GMT+0:00',
                    'fanvil_location': 'Default',
                    'fanvil_time_zone_name': 'GMT',
                    'fanvil_enable_dst': '0',
                    'fanvil_greeting': f'Bienvenido {phone_data.get("account.1.user_id", "Usuario")}'
                }
                value = defaults.get(var, '')
            config_content = config_content.replace(placeholder, str(value))
    
    # Eliminar líneas vacías sobrantes
    lines = config_content.split('\n')
    cleaned_lines = []
    prev_empty = False
    
    for line in lines:
        is_empty = line.strip() == ''
        if is_empty and prev_empty:
            continue  # Skip consecutive empty lines
        cleaned_lines.append(line)
        prev_empty = is_empty
    
    config_content = '\n'.join(cleaned_lines)
    
    return config_content


def create_config_file(mac_address, phone_data, template, output_dir):
    """
    Genera un archivo de configuración XML para un dispositivo Fanvil específico
    """
    # Crear el contenido del archivo de configuración
    config_content = create_config_from_data(template, phone_data)
    
    # Nombre del archivo basado en la dirección MAC
    filename = f"{mac_address.replace(':', '').replace('-', '').lower()}.xml"
    filepath = os.path.join(output_dir, filename)
    
    # Escribir el archivo
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print(f"Archivo de configuración generado: {filepath}")
    return filepath


def read_phone_data_from_csv(csv_file):
    """Lee los datos de los teléfonos desde un archivo CSV"""
    phones = []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Limpiar espacios en blanco de los valores
            cleaned_row = {k: v.strip() if v else '' for k, v in row.items()}
            phones.append(cleaned_row)
    
    return phones


def read_phone_data_from_json(json_file):
    """Lee los datos de los teléfonos desde un archivo JSON"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'phones' in data:
            return data['phones']
        else:
            return [data]  # Suponemos que es un solo teléfono


def main():
    parser = argparse.ArgumentParser(description='Generador de archivos de configuración XML para Fanvil en lote')
    parser.add_argument('--template', default='/workspace/fanvil-template.xml', help='Ruta a la plantilla XML (por defecto: /workspace/fanvil-template.xml)')
    parser.add_argument('--csv', help='Archivo CSV con datos de teléfonos')
    parser.add_argument('--json', help='Archivo JSON con datos de teléfonos')
    parser.add_argument('--output-dir', default='/workspace/configs', help='Directorio de salida (por defecto: /workspace/configs)')
    parser.add_argument('--single', action='store_true', help='Generar un solo archivo de configuración')
    parser.add_argument('--mac', help='Dirección MAC (requerido si se usa --single)')
    parser.add_argument('--account1_user_id', help='Usuario SIP cuenta 1 (requerido si se usa --single)')
    parser.add_argument('--account1_password', help='Contraseña SIP cuenta 1 (requerido si se usa --single)')
    parser.add_argument('--account1_server_address', help='Servidor SIP cuenta 1 (requerido si se usa --single)')
    
    args = parser.parse_args()
    
    # Cargar la plantilla
    if not os.path.exists(args.template):
        print(f"Error: No se encontró la plantilla en {args.template}")
        return
    
    template = load_template(args.template)
    
    # Asegurarse de que el directorio de salida exista
    os.makedirs(args.output_dir, exist_ok=True)
    
    if args.single:
        # Modo individual
        if not args.mac or not args.account1_user_id or not args.account1_password or not args.account1_server_address:
            print("Error: Para el modo individual, se requieren --mac, --account1_user_id, --account1_password y --account1_server_address")
            return
        
        phone_data = {
            'account.1.user_id': args.account1_user_id,
            'account.1.password': args.account1_password,
            'account.1.server_address': args.account1_server_address,
            'account.1.display_name': args.account1_user_id,
            'account.1.auth_id': args.account1_user_id,
            'account.1.sip_port': '5060',
            'account.1.register_expires': '3600',
            'account.1.outbound_proxy_primary': '',
            'account.1.outbound_proxy_secondary': '',
            'account.1.sip_transport': 'udp',
            'fanvil_server_name': args.account1_server_address,
            'dns_server_primary': '8.8.8.8',
            'dns_server_secondary': '8.8.4.4',
            'ntp_server_primary': 'pool.ntp.org',
            'ntp_server_secondary': 'time.nist.gov',
            'fanvil_time_zone': 'GMT+0:00',
            'fanvil_location': 'Default',
            'fanvil_time_zone_name': 'GMT',
            'fanvil_enable_dst': '0',
            'fanvil_greeting': f'Bienvenido {args.account1_user_id}',
            'fanvil_time_display': '0',
            'fanvil_date_display': '0',
            'http_auth_username': '',
            'http_auth_password': '',
            'domain_name': 'example.com'
        }
        
        create_config_file(args.mac, phone_data, template, args.output_dir)
        
    else:
        # Modo lote
        if args.csv:
            phone_data_list = read_phone_data_from_csv(args.csv)
        elif args.json:
            phone_data_list = read_phone_data_from_json(args.json)
        else:
            print("Error: Debe especificar un archivo --csv o --json con los datos de los teléfonos")
            return
        
        print(f"Procesando {len(phone_data_list)} teléfonos...")
        
        for i, phone_data in enumerate(phone_data_list):
            mac = phone_data.get('mac_address', phone_data.get('mac', f'00000000000{i:02d}'))
            
            # Asegurarse de que todos los campos necesarios estén presentes
            required_fields = [
                'account.1.user_id', 'account.1.password', 'account.1.server_address',
                'account.1.display_name', 'account.1.auth_id'
            ]
            
            for field in required_fields:
                if field not in phone_data or not phone_data[field]:
                    phone_data[field] = phone_data.get(field, '')
            
            # Establecer valores por defecto si no están presentes
            defaults = {
                'account.1.sip_port': '5060',
                'account.1.register_expires': '3600',
                'account.1.outbound_proxy_primary': '',
                'account.1.outbound_proxy_secondary': '',
                'account.1.sip_transport': 'udp',
                'fanvil_server_name': phone_data.get('account.1.server_address', 'sip.example.com'),
                'dns_server_primary': '8.8.8.8',
                'dns_server_secondary': '8.8.4.4',
                'ntp_server_primary': 'pool.ntp.org',
                'ntp_server_secondary': 'time.nist.gov',
                'fanvil_time_zone': 'GMT+0:00',
                'fanvil_location': 'Default',
                'fanvil_time_zone_name': 'GMT',
                'fanvil_enable_dst': '0',
                'fanvil_greeting': f'Bienvenido {phone_data.get("account.1.user_id", "Usuario")}',
                'fanvil_time_display': '0',
                'fanvil_date_display': '0',
                'http_auth_username': '',
                'http_auth_password': '',
                'domain_name': 'example.com'
            }
            
            for key, default_value in defaults.items():
                if key not in phone_data or not phone_data[key]:
                    phone_data[key] = default_value
            
            create_config_file(mac, phone_data, template, args.output_dir)
    
    print(f"Proceso completado. Archivos generados en: {args.output_dir}")


if __name__ == "__main__":
    main()