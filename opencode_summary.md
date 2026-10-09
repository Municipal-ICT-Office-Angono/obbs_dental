# OBBS Dental — Session Summary

## Objective
- Ship a containerized Odoo 19 demo DB for `obbs_dental` (DONE, verified).
- Build a standalone iPad/iOS-12-compatible HTML+CSS+JS replica of the 5-step dental patient intake form (NEW, demo-verified, prod NOT deployed).

## What was just done (mobile intake feature)
- `controllers/intake.py` rewritten: shared `_collect_and_validate` / `_create_from_intake`; new routes `GET /intake-mobile` (raw-HTML template, no `/web/assets/`) and `POST /intake-mobile/submit` (`type='json'`, CSRF-exempt).
- `views/intake_mobile_templates.xml` added (685 lines): raw `<html>` template `intake_mobile_page`, inline CSS + CDATA JS. **iOS 12 Safari-safe**: no `?.`/`??`, no Pointer Events (touch + mouse fallback), no flex `gap`, no `requestSubmit()`. Signature canvases 600x200 via `touchstart/move` + `preventDefault`; localStorage draft `obbs_intake_draft_v1` (excludes signatures); XHR POST JSON; multi-step error banner + thanks screen with reference.
- `__manifest__.py`: added `'views/intake_mobile_templates.xml'` after patient_intake_templates.
- Demo deploy steps that worked:
  - `docker exec obbs_dental_odoo odoo --db_host=db --db_port=5432 --db_user=odoo --db_password=odoo -d obbs_dental_demo -u obbs_dental --no-http --stop-after-init` (NOTE: bypassing the entrypoint means HOST/PORT/USER/PASSWORD env are NOT auto-translated — pass `--db_*` explicitly; also `--logfile` path is inside the container, not host).
  - `docker restart obbs_dental_odoo` to register routes.
- Demo verification (all PASS):
  - `GET /intake-mobile` → 200, 43.4 KB, ZERO `/web/assets/` references; contains form/honeypot/draft bar.
  - Happy-path JSON → `{"ok":true,"reference":"PAT/2026/00101","name":"Mobile Intake Test Guy"}`; DB row: patient 101, source=web_intake, intake_status=pending_review, 1 medical history, 2 consents.
  - Duplicate name+birthdate → rejected with existing record number.
  - Blank form → aggregated errors with `step` min.
  - Honeypot (`website` filled) → `ok:true, reference:false`, no record created.

## Demo environment (full, verified earlier)
- Containers: `obbs_dental_db` (postgres:16, healthy) + `obbs_dental_odoo` (odoo:19, port 8069, db-filter=obbs_dental_demo). Module mounted read-only `./:/mnt/extra-addons/obbs_dental:ro`.
- Logins: backend `admin`/`admin`; portal `deleon.jose@yahoo.com` / `Portal@123` (patient id 1 "Jose Gonzales De Leon", PAT/2026/00001).
- Demo counts: 100 patients, 100 medical histories, 157 dental histories, 192 visits, 297 service rels, 1706 tooth surfaces, 89 consents, 0 clinical findings.
- Patient numbering quirk: `ir_sequence` for dental.patient reset to number_next=101 via psql (module sequences are noupdate=1, never touch number_next). Portal test patient = PAT/2026/00001; random demo patients 00002–00100.

## Key operational details
- EVERY docker command needs `export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"`.
- Pre-approved temp dir: `/var/folders/y0/x5l9hjls1_35wn7x68kqwsh80000gn/T/opencode` (`/tmp/opencode` files vanish on macOS).
- macOS has no `grep -P` (use perl) and no `rg`; `bash -n` passes on both scripts.
- `scripts/setup_demo.sh` (5 steps, idempotent) + `scripts/destroy_demo.sh`; README has "Demo Environment (Docker)" section.
- Prod = `odoo19_prod` container / DB `obbsco.com`. Deploy upgrade: `docker exec odoo19_prod odoo -d obbsco.com -u obbs_dental --no-http --stop-after-init`; THEN `docker restart odoo19_prod` for controller/route changes. Template-only changes need upgrade alone.
- JS/SS asset changes need `DELETE FROM ir_attachment WHERE url LIKE '/web/assets/%'` before upgrade.

## Mobile intake design notes (preserve)
- Field NAMES match the web form exactly so shared `_collect_and_validate` handles both.
- `_valid_signature` strips `data:image` prefix, caps 500 KB, base64-validates.
- Duplicate check: last_name+first_name+birthdate (ilike) against existing demo patients.
- JSON route returns `{'ok', 'errors':[{step,msg}], 'step'}` / `{'ok', 'reference', 'name'}`.
- Unmapped conditions → `medical_conditions` text; allergies → `allergies` text; DOH booleans mapped via `_CONDITION_OPTIONS`.
- Creates on submit (sudo): `dental.patient` (source=web_intake, pending_review) → `dental.medical.history` (DOH booleans) → 2 `dental.consent` (data_privacy + waiver, state=signed) → best-effort `_create_customer_partner()`.

## Dashboard (Oral Health, backend) — in progress
- OWL 19 gotchas hit so far: (1) every `t-foreach` needs a `t-key` (else `OwlError: Directive t-foreach should always be used with a t-key!`); (2) `String()`/`Number()` etc. are NOT available in OWL template expressions (`ctx.String is not a function` — move into component methods, e.g. `isSelectedYear(y)`); use `_index` implicit vars (`y_index`) or unique IDs (`p.id`, `section.key`) as keys; (3) **inline arrow handlers in `t-on-click`/`t-on-change` do NOT fire in this build** — ALL handlers must be bare method references (`t-on-click="onCardClick"`) that read arguments via `t-att-data-*` attributes (`ev.currentTarget.dataset.drill`) — proven pattern (`onSvgClick` in odontogram). Chart clicks likewise NOT via `options.onClick` — use a method reference `t-on-click="onCanvasClick"` on the `<canvas>` and `chart.getElementsAtEventForMode(ev, "nearest"/"index", {...})`.
- Drill-down added: KPI cards clickable (`kpi:<key>` → `patients_by_kpi`), chart bars clickable (age `key` → `patients_by_group`). `onDrill(key)` toggles `state.drillKey`; card highlighted via `t-att-class` border-primary when active; `drillLabel()`/`drillPatients()` branch on the `kpi:` prefix.
- Backend: `_build_period_context` now also returns `patient_conditions` + `visit_services`; `get_dashboard_data` adds `patients_by_kpi` (attended/male/female/pregnant/with_caries/procedures) using `preg_total` set for pregnant, `'D' in patient_conditions` for caries, non-empty `visit_services` for procedures. Verified: KPI card counts == drill patient-list lengths for Jan 2026.
- OWL template/quirk notes for `dashboard.xml`: `bgConf<select>` options use component methods for `selected`; arrows in `t-on-click` OK.
- Goal: backend dashboard from Form-2 data; totals by age group; filter month/quarter/year; drill-down to patients. User chose: backend menu only, patient-list drill-down, KPI cards + Chart.js + form-row tables.
- `report/oral_health_report.py` refactored: `_build_period_context()` extracted (shared) + `_compute_all_rows()` now returns `(row_data, patient_sets)`; `_fill_sheet()` thin (Excel path unchanged — verified identical). Added `get_dashboard_data()` returning `{period_label, available_years, kpis(attended/male/female/pregnant/with_caries/procedures), groups(all 8 age incl pregnant), chart_groups(7 disjoint, excl pregnant), patients_by_group, sections(5 x rows w/ per-group + Total)}`.
- New `controllers/dashboard.py`: `GET /obbs/dashboard/data` (auth=user, http, plain JSON, 400 on bad params). Registered in `controllers/__init__.py`.
- New `static/src/js/dashboard.js` (OWL client action `obbs_dental_dashboard`, `loadBundle("web.chartjs_lib")`, fetch, Chart.js v4 stacked bars, drill-down table, open patient via action service) + `static/src/xml/dashboard.xml`.
- `views/menus.xml`: `ir.actions.client` + top-level `Dashboard` menu under Dental (sequence 9). `__manifest__.py`: dashboard.js in `web.assets_backend` (xml glob already covers template).
- Verified in demo: JSON endpoint returns correct data; `attended == male+female == sum(chart_groups)` for Jan/Q1/Annual; Excel JAN grand-totals match JSON exactly (attended 22, allergies 7, hypertension 2, caries 20, scaling 9) → no report regression; component + OWL template present in served `web.assets_web` bundle; no errors in server log.
- Deploy recipe that worked: delete `/web/assets/%` attachments ON THE **DB** container (`docker exec obbs_dental_db psql -U odoo -d obbs_dental_demo -c ...`), upgrade module, restart odoo container.
- PENDING: manual UI test by user (login admin → Dental > Dashboard). Not yet deployed to prod.

## Relevant files
- `controllers/intake.py` — rewritten, has `/intake-mobile` + `/intake-mobile/submit`.
- `views/intake_mobile_templates.xml` — NEW raw-HTML page.
- `__manifest__.py` — data includes intake_mobile_templates.xml (v1.5.0).
- `views/patient_intake_templates.xml` — existing web form (names/texts source of truth).
- `scripts/setup_demo.sh`, `scripts/destroy_demo.sh`, `docker-compose.yml`, `demo/demo_data.py`, `README.md`, `AGENTS.md`.

## Next move
- Optionally deploy to prod (`odoo19_prod`, DB `obbsco.com`): upgrade + `docker restart odoo19_prod`, verify `/intake-mobile` GET (200, no /web/assets) + one JSON submit per AGENTS deploy rules. Have NOT done this yet (awaiting user confirmation).
- Then update `README.md`/`AGENTS.md` with the mobile intake feature + iOS 12 compat rules; add portal card SVG icons polish item when desired.