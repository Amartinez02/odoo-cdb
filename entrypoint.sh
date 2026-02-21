#!/bin/bash

set -e

# Set database environment variables
: ${HOST:=${DB_PORT_5432_TCP_ADDR:='db'}}
: ${PORT:=${DB_PORT_5432_TCP_PORT:=5432}}
: ${USER:=${DB_ENV_POSTGRES_USER:=${POSTGRES_USER:='odoo'}}}
: ${PASSWORD:=${DB_ENV_POSTGRES_PASSWORD:=${POSTGRES_PASSWORD:='odoo'}}}

# Install required packages
apt-get update && \
apt-get install -y poppler-utils inotify-tools && \
apt-get clean

# Configure database arguments
DB_ARGS=()
function check_config() {
    param="$1"
    value="$2"
    if grep -q -E "^\s*\b${param}\b\s*=" "$ODOO_RC" ; then
        value=$(grep -E "^\s*\b${param}\b\s*=" "$ODOO_RC" |cut -d " " -f3|sed 's/["\n\r]//g')
    fi;
    DB_ARGS+=("--${param}")
    DB_ARGS+=("${value}")
}
check_config "db_host" "$HOST"
check_config "db_port" "$PORT"
check_config "db_user" "$USER"
check_config "db_password" "$PASSWORD"

# Function to start Odoo
function start_odoo() {
    wait-for-psql.py ${DB_ARGS[@]} --timeout=30
    exec odoo "${DB_ARGS[@]}" &
    ODOO_PID=$!
}

# Start Odoo initially
start_odoo

# Monitor changes in /mnt directories, ignoring .pyc files, __pycache__ folders, and .tmp files
inotifywait -m -r -e modify,create,delete /mnt/ |
grep --line-buffered -v -E '\.pyc$|__pycache__|\.tmp$' |

while read -r path _ file; do
    # Verificar si el archivo tiene extensión .py
    if [[ "$file" == *.py ]]; then
        echo "Change detected in $path$file. Restarting Odoo..."

        # Envía la señal TERM para un cierre seguro
        kill -TERM $ODOO_PID  

        # Espera hasta que el proceso termine
        while kill -0 $ODOO_PID 2>/dev/null; do
            sleep 1  # Comprueba cada segundo si el proceso ha terminado
        done

        # Reinicia Odoo
        start_odoo  # Asegúrate de que este comando o función esté definido correctamente
    fi
done

exit 1
