#!/usr/bin/env bash
set -e

CONF_FILE="/etc/odoo/odoo.conf"
CONF_DIR="/etc/odoo"
TARGET_CONF="$CONF_FILE"

# Check if target config directory/file is writable by the odoo user; if not, use /tmp/odoo.conf
if [ ! -w "$CONF_DIR" ] && [ ! -w "$CONF_FILE" ] 2>/dev/null; then
    TARGET_CONF="/tmp/odoo.conf"
fi

if [ -f "$CONF_FILE" ] && [ "$TARGET_CONF" != "$CONF_FILE" ]; then
    cp "$CONF_FILE" "$TARGET_CONF"
elif [ ! -f "$TARGET_CONF" ]; then
    cat <<EOF > "$TARGET_CONF"
[options]
addons_path = /mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons
data_dir = /var/lib/odoo
EOF
fi

# Function to update or append configuration key = value in the target conf
set_config_opt() {
    local key="$1"
    local val="$2"
    if [ -n "$val" ]; then
        if grep -q "^[[:space:]]*${key}[[:space:]]*=" "$TARGET_CONF" 2>/dev/null; then
            sed -i "s|^[[:space:]]*${key}[[:space:]]*=.*|${key} = ${val}|g" "$TARGET_CONF"
        else
            echo "${key} = ${val}" >> "$TARGET_CONF"
        fi
    fi
}

# Apply environment configuration to odoo.conf
set_config_opt "admin_passwd" "${ODOO_ADMIN_PASSWORD}"
set_config_opt "proxy_mode" "${PROXY_MODE:-True}"
set_config_opt "list_db" "${LIST_DB:-False}"
set_config_opt "dbfilter" "${DB_FILTER}"
set_config_opt "db_name" "${DB_NAME}"
set_config_opt "db_host" "${HOST:-${DB_HOST:-db}}"
set_config_opt "db_port" "${PORT:-${DB_PORT:-5432}}"
set_config_opt "db_user" "${USER:-${DB_USER:-odoo}}"
set_config_opt "db_password" "${PASSWORD:-${DB_PASSWORD}}"
set_config_opt "workers" "${ODOO_WORKERS:-2}"
set_config_opt "max_cron_threads" "${MAX_CRON_THREADS:-1}"
set_config_opt "limit_time_cpu" "${LIMIT_TIME_CPU:-600}"
set_config_opt "limit_time_real" "${LIMIT_TIME_REAL:-1200}"

# If fallback config location was used, set ODOO_RC so Odoo loads it
if [ "$TARGET_CONF" != "/etc/odoo/odoo.conf" ]; then
    export ODOO_RC="$TARGET_CONF"
fi

# Automatic Database Initialization on Fresh Deployment:
# If starting the main odoo service against a newly created blank DB,
# automatically run initial schema installation (-i obbs_dental --without-demo=all)
FIRST_ARG="${1:-odoo}"
if [ "$FIRST_ARG" = "odoo" ] && [ -n "${DB_NAME}" ]; then
    DB_STATUS=$(python3 -c "
import sys, time, psycopg2
host = '${HOST:-db}'
port = int('${PORT:-5432}')
user = '${USER:-odoo}'
password = '''${PASSWORD}'''
dbname = '${DB_NAME}'

for _ in range(30):
    try:
        conn = psycopg2.connect(host=host, port=port, user=user, password=password, dbname=dbname, connect_timeout=3)
        cur = conn.cursor()
        cur.execute(\"SELECT 1 FROM information_schema.tables WHERE table_name = 'ir_module_module'\")
        has_table = cur.fetchone() is not None
        conn.close()
        print('INITIALIZED' if has_table else 'UNINITIALIZED')
        sys.exit(0)
    except psycopg2.OperationalError:
        time.sleep(2)
    except Exception as e:
        print('ERROR')
        sys.exit(0)
print('TIMEOUT')
" 2>/dev/null || echo "SKIP")

    if [ "$DB_STATUS" = "UNINITIALIZED" ]; then
        echo "============================================================"
        echo " Fresh database '${DB_NAME}' detected."
        echo " Auto-initializing core schema and installing obbs_dental..."
        echo " (This is a one-time process on initial deployment)..."
        echo "============================================================"
        /entrypoint.sh odoo -d "${DB_NAME}" -i obbs_dental --without-demo=all --stop-after-init
        echo "==> Database initialization completed successfully!"
    fi
fi

# Hand over execution to official Odoo entrypoint
exec /entrypoint.sh "$@"
