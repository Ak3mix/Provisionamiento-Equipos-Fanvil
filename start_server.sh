#!/bin/bash

echo "Iniciando el sistema de autoprovisionamiento Fanvil..."

# Instalar dependencias si es necesario
if [ -f "requirements.txt" ]; then
    echo "Instalando dependencias..."
    pip install -r requirements.txt
fi

# Crear directorios necesarios
mkdir -p config

# Iniciar la aplicación Flask
echo "Iniciando servidor en http://0.0.0.0:5000"
python app.py