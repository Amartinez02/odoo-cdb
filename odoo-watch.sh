#!/bin/bash

# Instala inotify-tools si no están instalados
apt-get update && apt-get install -y inotify-tools

# Inicia el servidor Odoo
odoo --dev=all &

# Monitorea cambios en los archivos dentro del directorio de addons
while inotifywait -r -e modify /mnt/; do
    echo "Archivo modificado. Reiniciando Odoo..."
    pkill -f odoo    # Detener el proceso de Odoo
    odoo --dev=all & # Reiniciar el servidor Odoo
done
