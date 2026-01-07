# Guía de Uso del Sistema de Autoprovisionamiento Fanvil

## Introducción

Este sistema permite configurar automáticamente dispositivos Fanvil SIP a través de un servidor HTTP. Los dispositivos descargarán su configuración específica basada en su dirección MAC.

## Componentes del sistema

1. **Servidor HTTP**: Sirve los archivos de configuración
2. **Archivos de configuración**: Contienen los parámetros específicos para cada dispositivo
3. **Scripts auxiliares**: Ayudan a generar y gestionar las configuraciones

## Instalación y configuración

### 1. Preparar el entorno

Asegúrese de tener Python 3 instalado en su sistema.

### 2. Iniciar el servidor de aprovisionamiento

```bash
cd /workspace/fanvil-provisioning
python provision_server.py
```

El servidor se iniciará en el puerto 8000.

### 3. Generar archivos de configuración

Para generar un archivo de configuración para un dispositivo específico:

```bash
cd scripts
python generate_config.py --mac 00:11:22:33:44:55 --username usuario123 --password pass123 --server sip.miempresa.com
```

Esto creará un archivo `001122334455.cfg` en el directorio `../config`.

### 4. Configurar el dispositivo Fanvil

Configure el dispositivo para que obtenga su configuración desde el servidor:

- URL de autoprovisionamiento: `http://[IP_SERVIDOR]:8000/`
- El dispositivo buscará un archivo con su dirección MAC como nombre (por ejemplo: `001122334455.cfg`)

## Personalización

### Archivos de configuración

Puede personalizar los archivos de configuración según sus necesidades. Algunos parámetros importantes:

- `account.1.username`: Nombre de usuario SIP
- `account.1.password`: Contraseña SIP
- `account.1.sip_server.1.address`: Servidor SIP
- `auto_provision.server`: URL del servidor de aprovisionamiento
- `network.lan.dhcp_mode`: Modo DHCP (1=activo, 0=estático)

### Scripts

Puede modificar los scripts para adaptarlos a sus necesidades específicas:

- `generate_config.py`: Genera archivos de configuración personalizados
- `provision_server.py`: Servidor HTTP para servir configuraciones

## Ejemplo práctico

Supongamos que desea aprovisionar un Fanvil X4:

1. Determine la dirección MAC del dispositivo: `AABBCCDDEEFF`
2. Genere la configuración:
   ```bash
   cd scripts
   python generate_config.py --mac AA:BB:CC:DD:EE:FF --username extension1 --password mypassword --server sip.miempresa.com
   ```
3. Inicie el servidor:
   ```bash
   cd ..
   python provision_server.py
   ```
4. Configure el dispositivo para que apunte a `http://[IP_SERVIDOR]:8000/`
5. El dispositivo descargará automáticamente `aabbccddeeff.cfg`

## Consideraciones de seguridad

- Cambie las contraseñas predeterminadas
- Use HTTPS en lugar de HTTP para entornos de producción
- Proteja el servidor de aprovisionamiento con autenticación si es necesario
- Monitoree los accesos al servidor (los registros se guardan en `logs/`)

## Solución de problemas

- Verifique que el servidor esté corriendo y accesible
- Asegúrese de que los archivos de configuración tengan los nombres correctos
- Confirme que las direcciones MAC estén en el formato correcto (sin separadores)
- Revise los registros en el directorio `logs/` para ver las solicitudes recibidas