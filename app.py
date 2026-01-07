from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
import json
import os
from datetime import datetime

app = Flask(__name__)

# Directorios
CONFIG_DIR = 'fanvil-provisioning/config'
DEVICES_FILE = 'devices.json'

def load_devices():
    if os.path.exists(DEVICES_FILE):
        with open(DEVICES_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_devices(devices):
    with open(DEVICES_FILE, 'w') as f:
        json.dump(devices, f, indent=2)

def get_mac_from_filename(filename):
    """Extrae la MAC del nombre de archivo (ej. sip.cfg001122334455 -> 00:11:22:33:44:55)"""
    if 'sip.cfg' in filename:
        mac_part = filename.replace('sip.cfg', '')
        if len(mac_part) == 12:  # MAC en formato sin separadores
            return ':'.join(mac_part[i:i+2] for i in range(0, 12, 2)).upper()
    return filename

def get_config_files():
    """Obtiene la lista de archivos de configuración existentes"""
    if not os.path.exists(CONFIG_DIR):
        return []
    config_files = []
    for filename in os.listdir(CONFIG_DIR):
        if filename.startswith('sip.cfg'):
            mac = get_mac_from_filename(filename)
            config_files.append({
                'filename': filename,
                'mac': mac,
                'path': os.path.join(CONFIG_DIR, filename),
                'modified': datetime.fromtimestamp(os.path.getmtime(os.path.join(CONFIG_DIR, filename))).strftime('%Y-%m-%d %H:%M:%S')
            })
    return sorted(config_files, key=lambda x: x['mac'])

@app.route('/')
def index():
    devices = load_devices()
    config_files = get_config_files()
    return render_template('index.html', devices=devices, config_files=config_files)

@app.route('/add_device', methods=['POST'])
def add_device():
    data = request.json
    devices = load_devices()
    
    mac = data.get('mac').replace(':', '').replace('-', '').replace('.', '').upper()
    if len(mac) != 12:
        return jsonify({'success': False, 'error': 'MAC inválida'})
    
    device_info = {
        'mac': data.get('mac'),
        'model': data.get('model'),
        'name': data.get('name'),
        'username': data.get('username'),
        'password': data.get('password'),
        'sip_server': data.get('sip_server'),
        'port': data.get('port', '5060'),
        'display_name': data.get('display_name', ''),
        'created_at': datetime.now().isoformat()
    }
    
    devices[mac] = device_info
    save_devices(devices)
    
    # Generar archivo de configuración
    generate_config_file(mac, device_info)
    
    return jsonify({'success': True})

@app.route('/edit_device/<mac>', methods=['POST'])
def edit_device(mac):
    original_mac = mac.replace(':', '').replace('-', '').replace('.', '').upper()
    data = request.json
    
    devices = load_devices()
    if original_mac in devices:
        device_info = {
            'mac': data.get('mac'),
            'model': data.get('model'),
            'name': data.get('name'),
            'username': data.get('username'),
            'password': data.get('password'),
            'sip_server': data.get('sip_server'),
            'port': data.get('port', '5060'),
            'display_name': data.get('display_name', ''),
            'created_at': devices[original_mac].get('created_at'),
            'updated_at': datetime.now().isoformat()
        }
        
        # Eliminar el dispositivo anterior si cambió la MAC
        new_mac = data.get('mac').replace(':', '').replace('-', '').replace('.', '').upper()
        if original_mac != new_mac:
            del devices[original_mac]
        
        devices[new_mac] = device_info
        save_devices(devices)
        
        # Regenerar archivo de configuración
        generate_config_file(new_mac, device_info)
        
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Dispositivo no encontrado'})

@app.route('/delete_device/<mac>', methods=['DELETE'])
def delete_device(mac):
    clean_mac = mac.replace(':', '').replace('-', '').replace('.', '').upper()
    devices = load_devices()
    
    if clean_mac in devices:
        del devices[clean_mac]
        save_devices(devices)
        
        # Eliminar archivo de configuración
        config_path = os.path.join(CONFIG_DIR, f'sip.cfg{clean_mac}')
        if os.path.exists(config_path):
            os.remove(config_path)
        
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Dispositivo no encontrado'})

@app.route('/generate_config/<mac>')
def generate_config(mac):
    clean_mac = mac.replace(':', '').replace('-', '').replace('.', '').upper()
    devices = load_devices()
    
    if clean_mac in devices:
        device_info = devices[clean_mac]
        generate_config_file(clean_mac, device_info)
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Dispositivo no encontrado'})

def generate_config_file(mac, device_info):
    """Genera archivo de configuración para un dispositivo específico"""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
    
    config_path = os.path.join(CONFIG_DIR, f'sip.cfg{mac}')
    
    # Plantilla de configuración para Fanvil
    config_content = f"""# Configuracion generada automaticamente para {device_info['name']} ({device_info['mac']})
# Modelo: {device_info['model']}
# Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# Configuracion SIP
account.1.enable = 1
account.1.label = {device_info['name']}
account.1.display_name = {device_info.get('display_name', device_info['name'])}
account.1.auth_name = {device_info['username']}
account.1.password = {device_info['password']}
account.1.sip_server = {device_info['sip_server']}
account.1.port = {device_info['port']}

# Configuracion de red
network.lan.ip_assignment = dhcp
"""
    
    with open(config_path, 'w') as f:
        f.write(config_content)

@app.route('/config/<filename>')
def download_config(filename):
    """Sirve archivos de configuración"""
    return send_from_directory(CONFIG_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
    app.run(debug=True, host='0.0.0.0', port=5000)