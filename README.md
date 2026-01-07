# Sistema de Autoprovisionamiento Fanvil

Sistema web para el autoprovisionamiento de dispositivos SIP Fanvil con interfaz gráfica intuitiva.

## Características

- Interfaz web intuitiva para gestionar dispositivos Fanvil
- Soporte para múltiples modelos de Fanvil
- Generación automática de archivos de configuración
- Gestión completa de dispositivos (agregar, editar, eliminar)
- Visualización de archivos de configuración generados

## Requisitos

- Python 3.7 o superior
- Flask
- Jinja2
- Werkzeug

## Instalación

1. Clonar o descargar el proyecto
2. Instalar las dependencias:

```bash
pip install -r requirements.txt
```

3. Iniciar el servidor:

```bash
./start_server.sh
```

O alternativamente:

```bash
python app.py
```

## Uso

1. Acceder a la interfaz web en `http://localhost:5000`
2. Utilizar el botón "Agregar Dispositivo" para registrar nuevos dispositivos
3. Completar los datos del dispositivo (MAC, modelo, credenciales SIP, etc.)
4. El sistema generará automáticamente el archivo de configuración correspondiente
5. Los dispositivos Fanvil pueden descargar su configuración específica usando su dirección MAC

## Configuración de Dispositivos Fanvil

Para que los dispositivos Fanvil se aprovisionen automáticamente:

1. Configurar el servidor de aprovisionamiento en el teléfono con la URL: `http://[IP_SERVIDOR]:5000/config/sip.cfg[MAC_DISPOSITIVO]`
2. El dispositivo descargará su archivo de configuración personalizado basado en su dirección MAC

## Estructura de Directorios

```
/workspace/
├── app.py              # Aplicación Flask principal
├── requirements.txt     # Dependencias de Python
├── start_server.sh      # Script de inicio
├── templates/           # Plantillas HTML
│   └── index.html       # Página principal
├── config/              # Archivos de configuración generados
├── devices.json         # Base de datos de dispositivos
└── README.md            # Documentación
```

## Modelos Soportados

- Fanvil X4, X5, X6, X7, X8, X9, X10
- Fanvil E2, E3, E5
- Fanvil V62, V63, V64, V65, V67, V68, V69, V71, V72, V73, V75, V76, V78, V79
- Fanvil T60, T61, T62, T63, T64, T65, T66, T67, T68, T69

## Seguridad

- Cambiar la contraseña predeterminada en producción
- Limitar el acceso al servidor de aprovisionamiento
- Usar HTTPS en entornos de producción