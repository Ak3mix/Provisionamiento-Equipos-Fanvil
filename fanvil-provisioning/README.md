# Sistema de Autoprovisionamiento Fanvil

Este sistema permite el autoprovisionamiento automático de dispositivos Fanvil SIP.

## Estructura de directorios

- `config/` - Archivos de configuración para los dispositivos
- `firmware/` - Imágenes de firmware (opcional)
- `logs/` - Registros del sistema de aprovisionamiento
- `scripts/` - Scripts auxiliares para el sistema

## Configuración de dispositivos Fanvil

Los dispositivos Fanvil pueden ser configurados para obtener automáticamente su configuración desde un servidor HTTP. La URL base para la configuración es normalmente:

`http://[servidor]/[mac_address].cfg`

Donde `[mac_address]` es la dirección MAC del dispositivo sin separadores (por ejemplo: 001122334455)

## Archivos de configuración

Los archivos de configuración siguen el formato de Fanvil y contienen parámetros como:

- Configuración SIP
- Parámetros de red
- Parámetros de audio
- Parámetros de funciones específicas del teléfono

## Uso

1. Coloque los archivos de configuración en el directorio `config/`
2. Configure el servidor HTTP para servir estos archivos
3. Configure los dispositivos Fanvil para apuntar al servidor de aprovisionamiento