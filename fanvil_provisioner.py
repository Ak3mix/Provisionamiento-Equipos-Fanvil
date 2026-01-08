#!/usr/bin/env python3
"""
Fanvil Distributed Provisioning Service (FDPS)
Aplicación para autoprovisionamiento de equipos Fanvil
"""

import os
import json
import hashlib
import sqlite3
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import ipaddress
import argparse
import getpass
from pathlib import Path
import ftplib
import http.server
import socketserver
import threading
import time


class DatabaseManager:
    """Gestor de base de datos para almacenar información de dispositivos y usuarios"""
    
    def __init__(self, db_path: str = "fanvil_provision.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializa la base de datos con las tablas necesarias"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de usuarios (Administrador, Agente, Cliente)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL, -- 'admin', 'agent', 'client'
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de dispositivos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mac_address TEXT UNIQUE NOT NULL,
                model TEXT NOT NULL,
                ip_address TEXT,
                firmware_version TEXT,
                status TEXT DEFAULT 'pending', -- 'pending', 'online', 'offline', 'configured'
                group_id INTEGER,
                client_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP
            )
        ''')
        
        # Tabla de grupos de configuración
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                config_template TEXT, -- JSON con la configuración base
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de logs de operaciones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                device_mac TEXT,
                operation TEXT NOT NULL, -- 'config_change', 'firmware_update', 'provision'
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_user(self, username: str, password: str, role: str):
        """Agrega un nuevo usuario"""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, password_hash, role)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def verify_user(self, username: str, password: str) -> Optional[Dict]:
        """Verifica credenciales de usuario"""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, username, role FROM users WHERE username = ? AND password_hash = ?",
            (username, password_hash)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'username': result[1],
                'role': result[2]
            }
        return None
    
    def add_device(self, mac_address: str, model: str, client_id: int = None):
        """Agrega un nuevo dispositivo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO devices (mac_address, model, client_id) VALUES (?, ?, ?)",
                (mac_address, model, client_id)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def get_device(self, mac_address: str) -> Optional[Dict]:
        """Obtiene información de un dispositivo por MAC"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM devices WHERE mac_address = ?",
            (mac_address,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'mac_address': result[1],
                'model': result[2],
                'ip_address': result[3],
                'firmware_version': result[4],
                'status': result[5],
                'group_id': result[6],
                'client_id': result[7],
                'created_at': result[8],
                'last_seen': result[9]
            }
        return None
    
    def update_device_status(self, mac_address: str, status: str, ip_address: str = None):
        """Actualiza el estado de un dispositivo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if ip_address:
            cursor.execute(
                "UPDATE devices SET status = ?, ip_address = ?, last_seen = CURRENT_TIMESTAMP WHERE mac_address = ?",
                (status, ip_address, mac_address)
            )
        else:
            cursor.execute(
                "UPDATE devices SET status = ?, last_seen = CURRENT_TIMESTAMP WHERE mac_address = ?",
                (status, mac_address)
            )
        
        conn.commit()
        conn.close()
    
    def add_log(self, user_id: int, device_mac: str, operation: str, details: str):
        """Agrega un registro de operación"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO logs (user_id, device_mac, operation, details) VALUES (?, ?, ?, ?)",
            (user_id, device_mac, operation, details)
        )
        conn.commit()
        conn.close()


class ConfigGenerator:
    """Generador de archivos de configuración para dispositivos Fanvil"""
    
    def __init__(self, config_dir: str = "config_files"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
    
    def generate_general_config(self, model: str, params: Dict) -> str:
        """Genera archivo de configuración general para un modelo"""
        filename = f"f0C00{model[1:]}00000.cfg"  # Ejemplo: f0C006200000.cfg para C62
        filepath = self.config_dir / filename
        
        # Convertir parámetros a formato CFG
        config_content = self._dict_to_cfg(params)
        
        with open(filepath, 'w') as f:
            f.write(config_content)
        
        return str(filepath)
    
    def generate_mac_specific_config(self, mac_address: str, params: Dict) -> str:
        """Genera archivo de configuración específico por MAC"""
        # Convertir MAC a minúsculas y eliminar separadores
        clean_mac = mac_address.lower().replace(':', '').replace('-', '')
        filename = f"{clean_mac}.cfg"
        filepath = self.config_dir / filename
        
        # Convertir parámetros a formato CFG
        config_content = self._dict_to_cfg(params)
        
        with open(filepath, 'w') as f:
            f.write(config_content)
        
        return str(filepath)
    
    def generate_xml_config(self, mac_address: str, params: Dict) -> str:
        """Genera archivo de configuración en formato XML"""
        clean_mac = mac_address.lower().replace(':', '').replace('-', '')
        filename = f"{clean_mac}.xml"
        filepath = self.config_dir / filename
        
        root = ET.Element("FanvilConfig")
        
        for key, value in params.items():
            param_elem = ET.SubElement(root, "param")
            param_elem.set("name", key)
            param_elem.set("value", str(value))
        
        # Guardar XML con formato
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ", level=0)
        tree.write(filepath, encoding="utf-8", xml_declaration=True)
        
        return str(filepath)
    
    def _dict_to_cfg(self, params: Dict) -> str:
        """Convierte diccionario de parámetros a formato CFG"""
        lines = []
        for key, value in params.items():
            lines.append(f"{key}={value}")
        return "\n".join(lines)
    
    def encrypt_config(self, filepath: str, encryption_key: str) -> str:
        """Cifra un archivo de configuración usando AES de 256 bits"""
        # En una implementación real, se usaría una biblioteca como cryptography
        # Por simplicidad, aquí solo se simula el proceso
        encrypted_filepath = f"{filepath}.enc"
        
        # Simulación de cifrado (en la realidad usaríamos AES)
        with open(filepath, 'rb') as f:
            content = f.read()
        
        # Simulación de cifrado (no es real, solo para demostración)
        encrypted_content = content  # Aquí iría la lógica real de cifrado
        
        with open(encrypted_filepath, 'wb') as f:
            f.write(encrypted_content)
        
        return encrypted_filepath


class ProvisioningEngine:
    """Motor de aprovisionamiento para gestión de dispositivos"""
    
    def __init__(self, db_manager: DatabaseManager, config_generator: ConfigGenerator):
        self.db_manager = db_manager
        self.config_generator = config_generator
    
    def provision_device(self, mac_address: str, model: str, params: Dict, client_id: int = None) -> bool:
        """Provisiona un dispositivo individual"""
        # Registrar dispositivo en base de datos
        device_exists = self.db_manager.get_device(mac_address)
        if not device_exists:
            self.db_manager.add_device(mac_address, model, client_id)
        
        # Generar archivo de configuración específico
        config_file = self.config_generator.generate_mac_specific_config(mac_address, params)
        
        # Registrar operación
        user_id = 1  # Suponiendo usuario admin para este ejemplo
        self.db_manager.add_log(user_id, mac_address, 'provision', f"Config file generated: {config_file}")
        
        return True
    
    def provision_batch(self, devices: List[Dict], group_params: Dict) -> List[bool]:
        """Provisiona múltiples dispositivos"""
        results = []
        for device in devices:
            mac = device['mac_address']
            model = device['model']
            client_id = device.get('client_id')
            
            # Combinar parámetros generales con específicos del dispositivo
            params = {**group_params}
            if 'specific_params' in device:
                params.update(device['specific_params'])
            
            result = self.provision_device(mac, model, params, client_id)
            results.append(result)
        
        return results
    
    def update_firmware(self, mac_address: str, firmware_url: str) -> bool:
        """Actualiza firmware de un dispositivo"""
        # Registrar operación
        user_id = 1  # Suponiendo usuario admin
        self.db_manager.add_log(
            user_id, 
            mac_address, 
            'firmware_update', 
            f"Firmware update initiated from: {firmware_url}"
        )
        
        # En la realidad, aquí se enviaría la URL al dispositivo
        # para que descargue y actualice el firmware
        return True
    
    def add_to_group(self, mac_address: str, group_id: int) -> bool:
        """Agrega un dispositivo a un grupo de configuración"""
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE devices SET group_id = ? WHERE mac_address = ?",
            (group_id, mac_address)
        )
        conn.commit()
        conn.close()
        
        return True


class FanvilProvisioner:
    """Clase principal de la aplicación de aprovisionamiento"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.config_generator = ConfigGenerator()
        self.provisioning_engine = ProvisioningEngine(self.db_manager, self.config_generator)
        self.current_user = None
    
    def login(self, username: str, password: str) -> bool:
        """Inicia sesión de usuario"""
        user = self.db_manager.verify_user(username, password)
        if user:
            self.current_user = user
            return True
        return False
    
    def create_admin_user(self):
        """Crea el usuario administrador por defecto si no existe"""
        if not self.db_manager.verify_user('admin', 'admin'):
            self.db_manager.add_user('admin', 'admin', 'admin')
            print("Usuario administrador creado: admin/admin")
    
    def interactive_menu(self):
        """Menú interactivo para la aplicación"""
        self.create_admin_user()
        
        print("=== Fanvil Distributed Provisioning Service ===")
        print("Sistema de autoprovisionamiento de equipos Fanvil")
        print()
        
        # Solicitar credenciales
        username = input("Usuario: ")
        password = getpass.getpass("Contraseña: ")
        
        if not self.login(username, password):
            print("Credenciales inválidas")
            return
        
        print(f"Bienvenido {self.current_user['username']} ({self.current_user['role']})")
        print()
        
        while True:
            print("\n=== Menú Principal ===")
            print("1. Provisionar dispositivo individual")
            print("2. Provisionar por lotes")
            print("3. Ver dispositivos")
            print("4. Crear grupo de configuración")
            print("5. Añadir parámetros personalizados")
            print("6. Salir")
            
            choice = input("Seleccione una opción: ")
            
            if choice == '1':
                self._provision_individual()
            elif choice == '2':
                self._provision_batch()
            elif choice == '3':
                self._view_devices()
            elif choice == '4':
                self._create_group()
            elif choice == '5':
                self._add_custom_params()
            elif choice == '6':
                print("Saliendo...")
                break
            else:
                print("Opción inválida")
    
    def _provision_individual(self):
        """Provisionamiento individual de dispositivo"""
        print("\n--- Provisionamiento Individual ---")
        mac = input("Dirección MAC del dispositivo: ").strip()
        model = input("Modelo del dispositivo (ej. C62, X5, H5): ").strip()
        
        print("\nParámetros de configuración básicos:")
        params = {}
        
        # Parámetros SIP comunes
        params['sip_server'] = input("Servidor SIP: ").strip() or 'sip.example.com'
        params['sip_user'] = input("Usuario SIP: ").strip()
        params['sip_password'] = input("Contraseña SIP: ").strip()
        params['display_name'] = input("Nombre a mostrar: ").strip() or mac
        
        # Preguntar por parámetros adicionales
        if input("\n¿Desea añadir parámetros personalizados? (s/n): ").lower() == 's':
            while True:
                custom_key = input("Nombre del parámetro (o 'fin' para terminar): ").strip()
                if custom_key.lower() == 'fin':
                    break
                custom_value = input(f"Valor para {custom_key}: ").strip()
                params[custom_key] = custom_value
        
        # Provisionar dispositivo
        success = self.provisioning_engine.provision_device(mac, model, params)
        
        if success:
            print(f"\nDispositivo {mac} ({model}) provisionado exitosamente")
            print(f"Archivo de configuración generado")
        else:
            print("Error al provisionar el dispositivo")
    
    def _provision_batch(self):
        """Provisionamiento por lotes"""
        print("\n--- Provisionamiento por Lotes ---")
        
        # Parámetros comunes para todos los dispositivos
        print("Parámetros comunes para todos los dispositivos:")
        common_params = {}
        
        common_params['sip_server'] = input("Servidor SIP común: ").strip() or 'sip.example.com'
        common_params['display_name_prefix'] = input("Prefijo para nombres (opcional): ").strip() or ""
        
        print("\nIngrese dispositivos (uno por línea, 'fin' para terminar):")
        devices = []
        while True:
            mac = input("MAC del dispositivo (o 'fin'): ").strip()
            if mac.lower() == 'fin':
                break
            
            model = input(f"Modelo para {mac}: ").strip()
            
            # Parámetros específicos para este dispositivo
            specific_params = {}
            if input(f"¿Parámetros específicos para {mac}? (s/n): ").lower() == 's':
                sip_user = input(f"Usuario SIP para {mac}: ").strip()
                sip_password = input(f"Contraseña SIP para {mac}: ").strip()
                
                specific_params['sip_user'] = sip_user
                specific_params['sip_password'] = sip_password
            
            devices.append({
                'mac_address': mac,
                'model': model,
                'specific_params': specific_params
            })
        
        # Provisionar todos los dispositivos
        results = self.provisioning_engine.provision_batch(devices, common_params)
        
        print(f"\nResultado del provisionamiento por lotes:")
        for i, (device, result) in enumerate(zip(devices, results)):
            status = "ÉXITO" if result else "ERROR"
            print(f"{i+1}. {device['mac_address']} ({device['model']}): {status}")
    
    def _view_devices(self):
        """Ver lista de dispositivos"""
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT mac_address, model, ip_address, status, last_seen FROM devices")
        devices = cursor.fetchall()
        conn.close()
        
        print("\n--- Lista de Dispositivos ---")
        print(f"{'MAC Address':<20} {'Modelo':<10} {'IP':<15} {'Estado':<10} {'Última conexión':<20}")
        print("-" * 80)
        
        for device in devices:
            print(f"{device[0]:<20} {device[1]:<10} {device[2] or 'N/A':<15} {device[3]:<10} {device[4] or 'N/A':<20}")
    
    def _create_group(self):
        """Crear grupo de configuración"""
        print("\n--- Crear Grupo de Configuración ---")
        group_name = input("Nombre del grupo: ").strip()
        description = input("Descripción (opcional): ").strip()
        
        print("Parámetros de configuración para el grupo:")
        params = {}
        
        params['sip_server'] = input("Servidor SIP: ").strip() or 'sip.example.com'
        params['ntp_server'] = input("Servidor NTP: ").strip() or 'pool.ntp.org'
        
        # Preguntar por parámetros adicionales
        if input("\n¿Desea añadir parámetros personalizados al grupo? (s/n): ").lower() == 's':
            while True:
                custom_key = input("Nombre del parámetro (o 'fin' para terminar): ").strip()
                if custom_key.lower() == 'fin':
                    break
                custom_value = input(f"Valor para {custom_key}: ").strip()
                params[custom_key] = custom_value
        
        # Guardar grupo en base de datos
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO groups (name, description, config_template, created_by) VALUES (?, ?, ?, ?)",
            (group_name, description, json.dumps(params), self.current_user['id'])
        )
        conn.commit()
        group_id = cursor.lastrowid
        conn.close()
        
        print(f"Grupo '{group_name}' creado con ID {group_id}")
    
    def _add_custom_params(self):
        """Añadir parámetros personalizados"""
        print("\n--- Parámetros Personalizados Comunes ---")
        print("Estos son algunos parámetros avanzados que puedes usar:")
        print()
        print("Parámetros SIP:")
        print("  - sip_server: Servidor SIP primario")
        print("  - sip_port: Puerto SIP (por defecto 5060)")
        print("  - sip_transport: Transporte (UDP, TCP, TLS)")
        print("  - sip_outbound_proxy: Proxy de salida")
        print()
        print("Parámetros de red:")
        print("  - network_mode: Modo de red (DHCP, Static)")
        print("  - ip_address: Dirección IP estática")
        print("  - subnet_mask: Máscara de subred")
        print("  - gateway: Puerta de enlace")
        print("  - dns_server1: Servidor DNS primario")
        print("  - dns_server2: Servidor DNS secundario")
        print()
        print("Parámetros de audio:")
        print("  - codec_priority: Prioridad de códecs")
        print("  - dtmf_mode: Modo DTMF (RFC2833, SIP INFO)")
        print("  - echo_cancellation: Cancelación de eco (on/off)")
        print()
        print("Parámetros de seguridad:")
        print("  - admin_password: Contraseña de administrador")
        print("  - user_password: Contraseña de usuario")
        print("  - encryption: Cifrado (AES, None)")
        print()
        print("Parámetros de UI:")
        print("  - ring_tone: Tono de llamada")
        print("  - backlight_timeout: Tiempo de espera de retroiluminación")
        print("  - language: Idioma (en, es, fr, etc.)")
        print()
        print("Parámetros de función:")
        print("  - dss_keys: Configuración de teclas DSS")
        print("  - speed_dial: Marcación rápida")
        print("  - call_forward: Desvío de llamadas")
        print("  - call_waiting: Espera de llamadas")
        print()
        print("Para más información, consulta la documentación técnica de Fanvil.")


def main():
    """Función principal"""
    provisioner = FanvilProvisioner()
    provisioner.interactive_menu()


if __name__ == "__main__":
    main()