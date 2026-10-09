#!/usr/bin/env bash
#
# Tear down the OBBS Dental containerized demo:
#   - stop and remove the Odoo + PostgreSQL containers
#   - delete their named volumes (the demo database, odoo data)
#
# Usage:
#   ./scripts/destroy_demo.sh   (asks for confirmation)

set -euo pipefail
cd "$(dirname "$0")/.."

read -r -p "Remove the OBBS Dental demo containers AND volumes (demo database) permanently? [y/N] " confirm
case "${confirm:-N}" in
  y|Y|yes)
    docker compose down -v --remove-orphans
    echo "Containers and volumes removed."
    ;;
  *)
    echo "Cancelled - nothing was removed."
    ;;
esac