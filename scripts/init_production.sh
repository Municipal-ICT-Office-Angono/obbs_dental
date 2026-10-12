#!/usr/bin/env bash
#
# OBBS Dental - Production Deployment & Database Initialization Script
#
# Usage:
#   ./scripts/init_production.sh
#
# Prerequisites:
#   1. Copy .env.production.example to .env and configure passwords.
#   2. Docker and Docker Compose v2 installed.
#

set -euo pipefail
cd "$(dirname "$0")/.."

COMPOSE_FILE="docker-compose.prod.yml"

echo "============================================================"
echo " OBBS Dental - Production Deployment"
echo "============================================================"

# 1. Verify environment configuration
if [ -f ".env" ]; then
  ENV_FILE=".env"
elif [ -f ".env.production" ]; then
  ENV_FILE=".env.production"
else
  echo "ERROR: No .env or .env.production file found!"
  echo "Please copy .env.production.example to .env and customize your secrets:"
  echo "  cp .env.production.example .env"
  exit 1
fi

echo "==> Using environment configuration from: ${ENV_FILE}"
# Export env variables for shell usage (excluding comments)
set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a

DB_NAME="${POSTGRES_DB:-obbs_dental_prod}"
DB_USER="${POSTGRES_USER:-odoo_admin}"
NETWORK_NAME="${DOKPLOY_NETWORK:-dokploy-network}"

# 2. Ensure the Dokploy network exists
if ! docker network inspect "${NETWORK_NAME}" >/dev/null 2>&1; then
  echo "==> Creating external network '${NETWORK_NAME}'..."
  docker network create "${NETWORK_NAME}"
else
  echo "==> External network '${NETWORK_NAME}' found."
fi

# 3. Build production image with dependencies (openpyxl)
echo "==> Building production Odoo image..."
docker compose -f "${COMPOSE_FILE}" build

# 4. Start PostgreSQL and wait for health check
echo "==> Starting isolated PostgreSQL database..."
docker compose -f "${COMPOSE_FILE}" up -d db

echo "==> Waiting for PostgreSQL to become healthy..."
for i in $(seq 1 60); do
  STATUS=$(docker inspect -f '{{.State.Health.Status}}' obbs_dental_prod_db 2>/dev/null || echo "starting")
  if [ "${STATUS}" = "healthy" ]; then
    echo "    PostgreSQL is healthy!"
    break
  fi
  if [ "$i" -eq 60 ]; then
    echo "ERROR: PostgreSQL did not become healthy in 120 seconds."
    docker compose -f "${COMPOSE_FILE}" logs db --tail 50
    exit 1
  fi
  sleep 2
done

# 5. Check if production database exists
echo "==> Checking database '${DB_NAME}'..."
DB_EXISTS=$(docker compose -f "${COMPOSE_FILE}" exec -T db psql -U "${DB_USER}" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = '${DB_NAME}';" 2>/dev/null || echo "0")

if [ "${DB_EXISTS}" = "1" ]; then
  echo "==> Database '${DB_NAME}' already exists. Upgrading module obbs_dental..."
  MODE="-u"
else
  echo "==> Database '${DB_NAME}' does not exist. Initializing clean production database (WITHOUT demo data)..."
  MODE="-i"
fi

docker compose -f "${COMPOSE_FILE}" run --rm --no-deps odoo \
  odoo -d "${DB_NAME}" ${MODE} obbs_dental \
  --without-demo=all \
  --stop-after-init

# 6. Start the full production stack
echo "==> Starting full production stack..."
docker compose -f "${COMPOSE_FILE}" up -d

echo
echo "============================================================"
echo " OBBS Dental Production is Running!"
echo "------------------------------------------------------------"
echo "  Database          : ${DB_NAME}"
echo "  Container (Odoo)  : obbs_dental_prod_odoo"
echo "  Container (DB)    : obbs_dental_prod_db (Port 5432 isolated)"
echo "  Network Isolation : obbs_dental_prod_internal (internal: true)"
echo "  Dokploy Network   : ${NETWORK_NAME}"
echo "------------------------------------------------------------"
echo "  Endpoints (via configured Dokploy domain):"
echo "  Public intake     : /patient-intake"
echo "  Patient portal    : /my"
echo "  Backend login     : /web/login"
echo "------------------------------------------------------------"
echo "  IMPORTANT NEXT STEPS:"
echo "  1. Configure your domain in Dokploy (Domains tab -> Service: odoo, Port: 8069)."
echo "  2. Log in immediately as 'admin' and change the initial master/user password."
echo "  3. Set up automated database backups of volume 'obbs_dental_prod_db_data'."
echo "============================================================"
