#!/usr/bin/env bash
#
# Bootstrap a containerized Odoo 19 demo database for OBBS Dental.
#
# Steps performed:
#   1. Start PostgreSQL (and pull images on first run), wait until healthy.
#   2. Initialize a fresh database and install obbs_dental (creates schema,
#      views, portal pages, web intake route, DOH report).
#   3. Generate 100 demo patients with medical histories, dental conditions,
#      visits, dental history, and consents (skipped if patients exist).
#   4. Create the documented portal test account (deleon.jose@yahoo.com /
#      Portal@123) linked to a demo patient, if it does not exist yet.
#   5. Start the Odoo server on http://localhost:8069.
#
# Usage:
#   ./scripts/setup_demo.sh [DB_NAME]
#
# Defaults:
#   DB_NAME = obbs_dental_demo
#   Backend login is admin / admin (Odoo 19 defaults, not settable via CLI).
#
# Re-running is idempotent: if the database already exists the module is
# upgraded instead of reinstalled, and demo data is only generated once.

set -euo pipefail
cd "$(dirname "$0")/.."

DB_NAME="${1:-obbs_dental_demo}"

echo "==> [1/4] Starting PostgreSQL..."
docker compose up -d db

echo "==> Waiting for PostgreSQL to become healthy..."
for i in $(seq 1 60); do
  if [ "$(docker inspect -f '{{.State.Health.Status}}' obbs_dental_db 2>/dev/null)" = "healthy" ]; then
    break
  fi
  [ "$i" -eq 60 ] && { echo "ERROR: PostgreSQL did not become healthy in time."; docker compose logs db --tail 50; exit 1; }
  sleep 2
done

printf '\n==> [2/4] Preparing database "%s" and module obbs_dental\n' "$DB_NAME"
printf '    (first run pulls the odoo:19 image and initializes; this can take a few minutes)\n'
DB_EXISTS=$(docker compose exec -T db psql -U odoo -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = '${DB_NAME}';" | tr -d '[:space:]')
if [ "$DB_EXISTS" = "1" ]; then
  MODE="-u"
  printf '    Database exists -> upgrading obbs_dental\n'
else
  MODE="-i"
  printf '    Database does not exist -> installing obbs_dental\n'
fi
docker compose run --rm --no-deps odoo \
  odoo -d "${DB_NAME}" ${MODE} obbs_dental \
  --stop-after-init

printf '\n==> [3/4] Checking demo data...\n'
PATIENT_COUNT=$(docker compose exec -T db psql -U odoo -d "${DB_NAME}" -tAc "SELECT count(*) FROM dental_patient;" | tr -d '[:space:]')
if [ "${PATIENT_COUNT:-0}" -eq 0 ]; then
  echo "    Generating 100 demo patients (medical histories, dental conditions, visits, consents)..."
  docker compose run --rm --no-deps -T odoo \
    odoo shell -d "${DB_NAME}" --shell-interface=python <<'PYEOF'
env['dental.patient'].demo_generate()
env.cr.commit()
print("DEMO DATA: generated")
PYEOF
else
  echo "    ${PATIENT_COUNT} patients already present, skipping generation."
fi

printf '\n==> [4/5] Creating portal test account...\n'
docker compose run --rm --no-deps -T odoo \
  odoo shell -d "${DB_NAME}" --shell-interface=python <<'PYEOF'
login = 'deleon.jose@yahoo.com'
pwd = 'Portal@123'
users_env = env['res.users'].sudo().with_context(no_reset_password=True)
existing = users_env.search([('login', '=ilike', login)], limit=1)
if existing:
    print('PORTAL: account already exists, skipped')
else:
    patient = env['dental.patient'].search([('email', '=ilike', login)], limit=1)
    if not patient:
        patient = env['dental.patient'].create({
            'first_name': 'Jose Gonzales',
            'middle_name': 'D.',
            'last_name': 'De Leon',
            'birthdate': '1990-05-14',
            'sex': 'male',
            'nationality': 'Filipino',
            'religion': 'Roman Catholic',
            'email': login,
            'mobile': '09171234567',
            'home_address': '123 Rizal St, Brgy San Isidro\nAngono, Rizal',
        })
        env['dental.medical.history'].create({
            'patient_id': patient.id,
            'date': '2026-08-01',
            'general_health': 'Generally in good health',
            'current_medication': 'None',
            'allergies': 'None known',
            'medical_conditions': 'None',
            'smoking': False,
            'alcohol_use': False,
            'hypertension': False,
            'diabetes': False,
            'blood_disorders': False,
            'cardiovascular': False,
            'thyroid_disorders': False,
            'hepatitis': False,
            'malignancy': False,
            'hospitalization_history': False,
            'blood_transfusion': False,
            'betel_nut': False,
            'tattoo': False,
        })
        print('PORTAL: created demo patient %s %s' % (patient.patient_number, patient.display_name))
    partner = patient._create_customer_partner()
    user = users_env.create({
        'name': patient.display_name,
        'login': login,
        'email': login,
        'partner_id': partner.id,
        'group_ids': [(6, 0, [env.ref('base.group_portal').id])],
    })
    user.password = pwd
    print('PORTAL: created user %s linked to %s' % (login, patient.patient_number))
env.cr.commit()
PYEOF

printf '\n==> [5/5] Starting Odoo server...\n'
docker compose up -d odoo

echo
echo "============================================================"
echo " OBBS Dental demo is ready."
echo "------------------------------------------------------------"
echo "   Database   : ${DB_NAME}"
echo "   Backend    : http://localhost:8069/web/login"
echo "   Login      : admin"
echo "   Password   : admin"
echo "------------------------------------------------------------"
echo "   Public intake form : http://localhost:8069/patient-intake"
echo "   Portal login       : http://localhost:8069/web/login"
PORTAL_REF=$(docker compose exec -T db psql -U odoo -d "${DB_NAME}" -tAc \
  "SELECT p.patient_number || ' ' || p.display_name FROM dental_patient p JOIN res_partner rp ON rp.id = p.partner_id WHERE rp.email ILIKE 'deleon.jose%' LIMIT 1;" | tr -d '\r')
echo "   Portal test user   : deleon.jose@yahoo.com / Portal@123"
echo "        (${PORTAL_REF:-linked patient not found})"
echo "============================================================"