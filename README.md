# Fanvil Phone Configuration Generator

Este proyecto proporciona una solución para generar archivos de configuración XML para dispositivos Fanvil en lotes, simplificando la configuración de múltiples teléfonos IP.

## Características

- **Plantilla simplificada**: Solo los campos esenciales necesarios para la configuración del teléfono
- **Generación en lote**: Capacidad para procesar múltiples dispositivos desde archivos CSV o JSON
- **Procesamiento de condicionales**: Manejo correcto de secciones condicionales para cuentas SIP
- **Soporte para una o dos líneas**: Inclusión dinámica de la segunda cuenta según los datos proporcionados

## Estructura del proyecto

- `fanvil-template.xml`: Plantilla XML simplificada para dispositivos Fanvil
- `generate_fanvil_configs.py`: Script principal para generación en lote
- `sample_phones.csv`: Ejemplo de archivo CSV con datos de teléfonos
- `sample_phones.json`: Ejemplo de archivo JSON con datos de teléfonos

## Campos de configuración

La plantilla procesa los siguientes campos de configuración:

### Cuenta 1 (requerida)
- `account.1.user_id`: ID de usuario SIP
- `account.1.password`: Contraseña SIP
- `account.1.server_address`: Servidor SIP
- `account.1.display_name`: Nombre para mostrar
- `account.1.auth_id`: ID de autenticación
- `account.1.sip_port`: Puerto SIP (por defecto: 5060)
- `account.1.register_expires`: Tiempo de expiración de registro (por defecto: 3600)
- `account.1.outbound_proxy_primary`: Proxy saliente primario
- `account.1.outbound_proxy_secondary`: Proxy saliente secundario
- `account.1.sip_transport`: Transporte SIP (udp, tcp, tls, dns srv) (por defecto: udp)

### Cuenta 2 (opcional)
- `account.2.user_id`: ID de usuario SIP
- `account.2.password`: Contraseña SIP
- `account.2.server_address`: Servidor SIP
- `account.2.display_name`: Nombre para mostrar
- `account.2.auth_id`: ID de autenticación
- `account.2.sip_port`: Puerto SIP (por defecto: 5060)
- `account.2.register_expires`: Tiempo de expiración de registro (por defecto: 3600)
- `account.2.outbound_proxy_primary`: Proxy saliente primario
- `account.2.outbound_proxy_secondary`: Proxy saliente secundario
- `account.2.sip_transport`: Transporte SIP (udp, tcp, tls, dns srv) (por defecto: udp)

### Configuración general
- `mac_address`: Dirección MAC del dispositivo (para nombrar el archivo de configuración)
- `fanvil_server_name`: Nombre del servidor Fanvil
- `dns_server_primary`: Servidor DNS primario (por defecto: 8.8.8.8)
- `dns_server_secondary`: Servidor DNS secundario (por defecto: 8.8.4.4)
- `ntp_server_primary`: Servidor NTP primario (por defecto: pool.ntp.org)
- `ntp_server_secondary`: Servidor NTP secundario (por defecto: time.nist.gov)
- `fanvil_time_zone`: Zona horaria (por defecto: GMT+0:00)
- `fanvil_location`: Ubicación (por defecto: Default)
- `fanvil_time_zone_name`: Nombre de la zona horaria (por defecto: GMT)
- `fanvil_enable_dst`: Habilitar horario de verano (por defecto: 0)
- `fanvil_greeting`: Mensaje de bienvenida en la pantalla LCD
- `fanvil_time_display`: Formato de visualización de hora (por defecto: 0)
- `fanvil_date_display`: Formato de visualización de fecha (por defecto: 0)
- `http_auth_username`: Nombre de usuario para autenticación HTTP
- `http_auth_password`: Contraseña para autenticación HTTP
- `domain_name`: Nombre de dominio para actualización automática

## Uso

### Generación en lote desde CSV

```bash
python3 generate_fanvil_configs.py --csv sample_phones.csv --output-dir configs
```

### Generación en lote desde JSON

```bash
python3 generate_fanvil_configs.py --json sample_phones.json --output-dir configs
```

### Generación individual

```bash
python3 generate_fanvil_configs.py --single --mac 00:11:22:33:44:55 --account1_user_id 1001 --account1_password password123 --account1_server_address sip.example.com --output-dir configs
```

### Parámetros adicionales

- `--template`: Ruta a la plantilla XML personalizada (por defecto: fanvil-template.xml)
- `--output-dir`: Directorio de salida para los archivos generados (por defecto: configs)
- `--single`: Modo de generación individual
- `--mac`: Dirección MAC del dispositivo (requerido en modo individual)
- `--account1_*`: Parámetros para la primera cuenta en modo individual
- `--account2_*`: Parámetros para la segunda cuenta en modo individual

## Formato de los archivos de entrada

### CSV
El archivo CSV debe contener un encabezado con los nombres de los campos. Ejemplo:

```csv
mac_address,account.1.user_id,account.1.password,account.1.server_address,account.1.display_name,account.1.auth_id,account.1.sip_port,account.1.outbound_proxy_primary,account.2.user_id,account.2.password,account.2.server_address,account.2.display_name,account.2.auth_id
00:11:22:33:44:55,1001,password123,sip.example.com,Usuario 1001,1001,5060,proxy.example.com,1002,password456,sip.example.com,Usuario 1002,1002
```

### JSON
El archivo JSON puede contener un array de objetos con los datos de los teléfonos:

```json
{
  "phones": [
    {
      "mac_address": "00:11:22:33:44:55",
      "account.1.user_id": "1001",
      "account.1.password": "password123",
      "account.1.server_address": "sip.example.com",
      "account.1.display_name": "Usuario 1001",
      "account.1.auth_id": "1001",
      "account.1.sip_port": "5060",
      "account.1.outbound_proxy_primary": "proxy.example.com",
      "account.2.user_id": "1002",
      "account.2.password": "password456",
      "account.2.server_address": "sip.example.com",
      "account.2.display_name": "Usuario 1002",
      "account.2.auth_id": "1002"
    }
  ]
}
```

## Ventajas de esta solución

1. **Simplificación**: Elimina campos innecesarios del archivo de configuración original
2. **Eficiencia**: Permite configurar múltiples teléfonos rápidamente
3. **Flexibilidad**: Soporta configuración de una o dos líneas según sea necesario
4. **Automatización**: Facilita la integración con sistemas de aprovisionamiento automático
5. **Mantenibilidad**: Plantilla fácil de actualizar y mantener