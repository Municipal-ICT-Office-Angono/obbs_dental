# Agent Conventions

## Odoo 19 Specifics

- **Security groups**: Use `res.groups.privilege` pattern — `ir.module.category` → `res.groups.privilege` (via `category_id`) → `res.groups` (via `privilege_id`). Groups no longer have `category_id`/`category_ids` fields.
- **Search views**: Use `<group name="group_by">` with `<filter domain="[]" ...>` inside. No `expand`/`string` attributes on group element.
- **Commands**: Use `Command.link(ref(...))` or `eval="[(4, ref(...))]"` syntax.
- **This build's quirks (odev Odoo 19, `obbsco.com`)**: These differ from stock Odoo — verify before assuming standard API.
  - `res.users` uses **`group_ids`** (NOT `groups_id`). A pure portal user = create with `group_ids=[(6,0,[ref('base.group_portal')])]` only (no group_user). Check internals via `user.all_group_ids` (implies `base.group_user`). `partner_share` is auto-computed.
  - `portal` `res.users` has **NO `action_signup()`** and res.users/res.partner have no stored `signup_token`/`signup_url`. Invite flow = `partner.signup_prepare('signup')` + `ref('auth_signup.portal_set_password_email').send_mail(user.id)`. Signup link rendered via `partner._get_signup_url()`.
  - `res.partner` has **NO `mobile`, `birthdate`, `gender`** fields. Sync mobile→`phone`, home_address→`street`/`street2`; skip birthdate/gender on partner.
  - No `ir.actions.act_window_message` — use `{'type':'ir.actions.client','tag':'display_notification',...}` for button feedback.
  - Portal + auth_signup + website already installed on `obbsco.com`.

## Patient Portal (Milestone 5b — Phases 1-5 Done)

- **Portal home cards**: all four dental cards render via `t-call="portal.portal_docs_entry"` inside `portal_common_category` (template `portal_my_home`, inherit priority 40). Core portal JS unhides the icon wrapper (`o_portal_icon d-none` → `d-block`), so cards need BOTH an `icon` t-set (any SVG URL) AND `config_card=True` (or a `placeholder_count` from a cached portal counter) to avoid being hidden as "dynamic" cards. Icons are currently a shared placeholder (`/portal/static/src/img/portal-addresses.svg`) — replace with dental SVGs via the same `t-set="icon"` values.
- **Portal test account**: `deleon.jose@yahoo.com` / `Portal@123` → patient **PAT/2026/00310 Jose Gonzales De Leon** (patient id 308, partner 102, portal user uid 22). The only demo patient with `partner_id` set. Portal login via `/web/login` (or signup link).

- **Partner linkage**: `dental.patient.partner_id` + `_create_customer_partner()` / `_sync_partner()` in `models/dental_patient.py`. Patient write-hook re-syncs name/email/mobile/address to the linked `res.partner` (only non-empty values). `portal_user_ids` is a computed M2M (search via `res.users.partner_id`).
- **Invite button**: `action_create_portal_user()` on `dental.patient` (Manager group only) — creates/reuses partner (dedup by email), creates pure portal user (`group_ids=[portal]`), `signup_prepare('signup')`, sends `auth_signup.portal_set_password_email`. Guard: email required; reject if login taken by an internal user with a different partner.
- **Form**: `Portal Access` page on patient form (Manager group) with `partner_id` (readonly), `portal_user_ids`, invite button.
- **Portal reads**: portal users have ZERO ACL on `dental.*` (do not add ACLs). All future portal controllers must `sudo()` and filter strictly `[('partner_id','=',user.partner_id.id)]`.
- **Portal scaffolding (Phase 2)**: `controllers/portal.py` subclass `DentalPatientPortal(CustomerPortal)` with `_get_my_patient()` (sudo, scoped to `request.env.user.partner_id`), `_prepare_portal_layout_values()` injecting `patient` into every portal page, `_prepare_home_portal_values()` providing `patient_count`, and `@route('/my/patient', auth='user', website=True)` rendering `obbs_dental.portal_patient_overview`. Template `portal_my_home` (inherit `portal.portal_my_home`, priority 40) injects a `portal_docs_entry` card into `portal_common_category` shown `t-if="patient"`. Personal/contact/insurance+emergency info displayed; `partner_id` is HARD-LOCKED to `dental.patient` (no `partner_id` field on `res.partner`), so the link is purely via patient's `partner_id` — patient row must have `partner_id` set for the portal to find them.
- **Medical History page (Phase 3)**: route `/my/medical_history` renders `obbs_dental.portal_medical_history` (accordion per record, red/grey badges for each DOH boolean option). Portal templates are **server-side QWeb** — `t-attf-*` attributes only accept simple `name.attr` expressions (NO subscripts like `#{options[opt]}` or `getattr()` — they raise `ValueError: Can not compile expression` 500s); use `t-att-class`/`t-esc` with full expressions instead. `options` dict + labels live on the route; iterate `t-as="opt"` and read state via `rec[opt]`.
- **Deploy**: after any controller change the Odoo server must restart (`docker restart odoo19_prod`) or routes won't register; templates update on module upgrade alone.
- **Dental History page (Phase 4)**: route `/my/dental_history` renders `obbs_dental.portal_dental_history` — Visits accordion (services as badges, DOH indicator badges) + a Dental Treatment Records table from `dental.history` (condition badge colored inline via `t-att-style` using `cond_colors`, labels via `cond_labels`). Condition code→name/color dicts are built from `dental.condition` (NOT hardcoded). `dental.patient` has NO `visit_ids` field — query `dental.visit.search([('patient_id','=',patient.id)])` explicitly. Sort recordsets with `sorted(..., key=..., reverse=True)` (one2many order is unreliable).
- **Demo data**: `_create_demo_dental_history()` in `demo/demo_data.py` generates 1-4 `dental.history` rows for ~30% of patients, dated from their visits — needed because the chart widget data (`dental.tooth`/`dental.tooth.surface`) is separate from `dental.history`.
- **Dental Chart page (Phase 5)**: route `/my/dental_chart` renders `obbs_dental.portal_dental_chart` — a server-side read-only SVG mirroring the backend OWL widget. Geometry lives in `controllers/chart_geometry.py` (ported from `static/src/js/tooth_layout.js`: viewBox 1020x316, PX 56, midline X=510, y-rows 16/72/150/228, SURFACE_PATHS T/B/L/R/C). Controller builds `build_chart(patient)` with teeth list (52 FDI numbers in display order, each with prebuilt `transform` string + 5 surfaces `{path,color}` from the latest `dental.tooth.surface` per code) + legend (unique conditions with color/label). Store positions as **ints** and precompute the `translate(x,y)` string in Python — QWeb cannot concat str+int or call `str()` in expressions. Dict values must be accessed with `chart['key']` (NO `chart.key` attribute access in QWeb — raises AttributeError). Rendering uses only presentation attributes so no scss asset is needed.

## Development Status (Sep 2026)

**Complete**: Milestones 1 (foundation), 2 (intake), 3 (odontogram), 5a (demo data + DOH Form 2 report), 5b (patient portal, **Phases 1–5 all done**), **Public Patient Intake (web intake form at `/patient-intake`)**, and **Milestone 4 (Clinical Workflow)**.
**Next up**: Milestone 5 (Operations — scheduling, billing, payments, reports, dashboard). Portal polish items: replace the shared placeholder `t-set="icon"` on the four portal home cards with dental SVGs.

### Deploy reminders
- **Model changes** (new fields/models): always `docker restart odoo19_prod` after the upgrade. The `-u` upgrade runs in a separate process that updates the DB, but the long-running server keeps a **stale in-memory registry** — without a restart the web client throws `"..."."..." field is undefined` (OwlError / `Field.parseFieldNode`) even though the field exists in `ir_model_fields`.
- Controller changes: restart (routes register on boot).
- Template/`demo`/`view` changes: upgrade alone is enough (`docker exec odoo19_prod odoo -d obbsco.com -u obbs_dental --no-http --stop-after-init --logfile=/tmp/opencode/uNN.log`, EXIT 0 = clean).
- JS/SS asset changes: `DELETE FROM ir_attachment WHERE url LIKE '/web/assets/%'` then upgrade.
- `odoo shell` runs piped scripts in a **transaction that is rolled back** — add `env.cr.commit()` (or write + `env.cr.rollback()` for read-only checks) or your test data won't persist.

### How to continue (portal-related)
- Verify the portal live as `deleon.jose@yahoo.com` / `Portal@123` on `http://localhost:8069` with `Host: obbsco.com` header (dbfilter `%h`): `/my`, `/my/patient`, `/my/medical_history`, `/my/dental_history`, `/my/dental_chart`.
- Test scripts pattern in `/tmp/opencode/*.sh`: login via CSRF token extracted with `grep -oP 'name="csrf_token"[^>]*value="\K[^"]+'`, then curl the page with the cookie jar.
- After any controller change: `docker restart odoo19_prod` (routes register on boot). Template/`demo`/`view` changes: `docker exec odoo19_prod odoo -d obbsco.com -u obbs_dental --no-http --stop-after-init --logfile=/tmp/opencode/uNN.log` (EXIT 0 = clean).
- JS asset cache stomp (only for widget/JS asset changes): `DELETE FROM ir_attachment WHERE url LIKE '/web/assets/%'` then upgrade.
- New portal pages must: subclass `DentalPatientPortal`, `sudo()` in the route, scope searches to `request.env.user.partner_id.id`, add a `config_card=True` home card + `icon`, and keep portal users on **zero** `dental.*` ACLs.
- QWeb server-side rules for portal templates: `t-attf-*` = simple `name.attr` only; dict values via `['key']`; no `str()`/concat-with-int in expressions — precompute strings in Python.

## Dental Chart Widget (Milestone 3 — Completed)

- **Field widget**: `dental_chart` registered in `static/src/js/dental_chart.js` via `registry.category("fields").add("dental_chart", dentalChartField)` with `supportedTypes: ["text"]`
- **Template**: `obbs_dental.DentalChart` in `static/src/xml/dental_chart.xml` — SVG with viewBox `0 0 1180 500`, rendered inside `<div class="o_dental_chart">`
- **SVG sizing**: Use `width="100%"` as SVG attribute (not inline style). Parent wrapper must have `width: 100%; min-width: 100%` CSS
- **Click handling**: OWL's `t-on-click` on SVG children does NOT work. Instead use `t-on-click="onSvgClick"` on the `<svg>` root and compute which tooth was hit from mouse coordinates mapped through `getBoundingClientRect()` + viewBox math
- **Tooth data**: 32 FDI teeth (11-48) with positions in `TOOTH_POSITIONS` constant. Each tooth is a `<g transform="translate(x,y)">` containing `<path>` (the shape), `<text class="tooth-number">` (FDI number), and optionally `<text class="tooth-label">` (condition name)
- **Tooth paths**: Buccal-view silhouettes in `TOOTH_PATHS` constant — keys `incisor/lateral/canine/premolar/molar` each with `upper`/`lower` variants. Path viewBox is ~56×90 internal units
- **Conditions**: 23 codes (`PR/D/Am/Co/JC/In/S/M/MO/X/XO/Rf/Im/Un/Sp/BR/ABR/ABF/Imp/Abu/Att/Po/Rm`) with unique colors in `CONDITION_COLORS` and labels in `CONDITION_LABELS`
- **Dialog**: Custom `position: fixed` overlay (not Bootstrap modal) with `z-index: 10000`. Uses `<select>` with `t-att-selected` on matching `<option>`, `<input>` and `<textarea>` with `t-att-value`. All change handlers are individual methods (`onConditionChange`, `onTreatmentChange`, `onNotesChange`) — DO NOT use arrow function expressions in `t-on-change`
- **Save flow**: `saveTooth()` calls `orm.call("dental.history", "create_from_chart", [params])` then `orm.read("dental.patient", [resId], [fieldName])`. Writes `this.props.record.data[this.props.name] = jsonStr` to persist across tab switches
- **Data model**: `dental.patient.tooth_conditions` is a non-stored computed Text field (`compute='_compute_tooth_conditions'`, `store=False`). Method `create_from_chart` on `dental.history` creates records and recomputes the field
- **Error prevention**: Load assets cache: `DELETE FROM ir_attachment WHERE url LIKE '/web/assets/%'` followed by module upgrade

## Workflow Requirements

- Every completed milestone MUST include a test procedure so the user can verify functionality.
- Test procedures should be practical steps the user can follow in the Odoo UI, not automated tests.
- After the user confirms a milestone test is successful, update README.md's Development Roadmap to mark that milestone as completed.

## Demo Data & Reporting (Milestone 5a — Completed)

- **Demo data script**: `demo/demo_data.py` — defines `demo_generate()` method on `dental.patient` via `_inherit`. Call from Odoo shell: `env['dental.patient'].demo_generate()`
- **100 patients**: Realistic Filipino names, Angono Rizal addresses, age distribution across all DOH age groups (infant through senior)
- **28 conditions**: 23 original + 5 new DOH conditions (`Gi` Gingivitis, `PD` Periodontal Disease, `OD` Oral Debris, `Ca` Calculus, `DFA` Dento-Facial Anomaly)
- **10 services**: `dental.service` lookup table — SC/PF/TF/EX/GT/SE/FT/PO/AD/OS
- **New models**: `dental.service` (lookup), `dental.visit` (visit records with services M2M + DOH flags)
- **DOH boolean fields**: `dental.medical.history` now has `hypertension`, `diabetes`, `blood_disorders`, `cardiovascular`, `thyroid_disorders`, `hepatitis`, `malignancy`, `hospitalization_history`, `blood_transfusion`, `betel_nut`, `tattoo`
- **Report wizard**: `report.oral.health.wizard` — transient model with year, report_type (monthly/quarterly/annual), month, quarter, municipality, province fields
- **Report generator**: `report.oral.health.generator` — abstract model using `openpyxl` to copy the blank form template and fill cells with computed data
- **Template file**: `ANGONO 2026 blank form 2.xlsx` — DOH Oral Health Form 2 with 14 sheets (JAN-DEC + 4TH QTR + ANN)
- **Column mapping**: 39 demographic columns (Pregnant 10-14/15-19/20-49, Infant M/F, Under-5 ages 1-4 M/F + Total, School-age 5-9 M/F + Total, Adolescent 10-14/15-19 M/F, Adult 20-59 M/F, Senior 60+ M/F, Total M/F, Grand Total)
- **Row categories**: 50 data rows across 5 sections — Medical History (11), Dietary/Social (4), Oral Health + DMFT (13), Services Rendered (13), OFC (2)
- **Row function signature**: All `_row_*` functions MUST use uniform signature `(self, pset, data)` where `data` is the context dict (`patient_map`, `patient_latest_med`, `patient_conditions`, `patient_dmft`, `visit_services`, `visit_flags`). Never use positional argument lists — mismatch caused AttributeErrors.
- **Sheet mapping**: `SHEET_MAP['quarterly']` maps int keys 1-4 to `1ST/2ND/3RD/4TH QTR`. Never use string keys in `SHEET_MAP`.
- **Template integrity**: `ANGONO 2026 blank form 2.xlsx` is a READ-ONLY template. `generate_report()` loads it with `load_workbook` and saves ONLY to `/tmp/...` — NEVER `wb.save()` in place (previously polluted 5 sheets with test data; cleaned Sep 2026).
- **SSB estimate**: `_row_ssb` uses hardcoded `int(len(pset) * 0.35)` — no SSB field in models yet.
- **Dependency**: `openpyxl` Python package must be installed in the Odoo environment (`pip install openpyxl`)
- **Menu path**: Dental > Reports > Oral Health Form 2

## Clinical Workflow (Milestone 4 — Completed)

- **Model**: `dental.clinical.finding` (`models/dental_clinical_finding.py`) — one row per dentist screening/consultation. Mirrors the clinician-written sections of the DOH Individual Patient Treatment Record.
  - **A.1–A.5 clinical findings**: `periodontal_disease` (+ `periodontal_teeth`, `mobility` I/II/III), `torus_palatinus`, `torus_mandibularis`, `epulis_cyst_tumor`, prosthesis CD/RPD/FPD upper+lower booleans + `prosthesis_years`, `ridge_height_upper`/`ridge_height_lower` (normal/low).
  - **B.1–B.4 treatment plan**: `rx_root_planing_scaling`, `rx_extraction`, `rx_surgical_torus`, `rx_surgical_biopsy`, `rx_prosthesis_repair`, `rx_prosthesis_replacement`.
  - **Oral Health Status**: `teeth_with_caries`, `oral_debris_calculus`, `gingivitis_periodontitis`, `dento_facial_anomaly`, `soft_tissue_lesions`, `permanent_teeth_present`, `deciduous_teeth_present`, `oro_facial_anomaly` (+ `_type`), `oral_lesions` (+ `_type`), `assessed_by`/`assessed_position`.
  - **Notes/attachments**: `clinical_notes` (Text) + `attachment_ids` `Many2many('ir.attachment')` rendered with `widget="many2many_binary"` for X-rays/photos (widget verified present in this build's `web` module).
  - **Workflow**: `state` Selection `draft`/`done` (statusbar) + `action_confirm()`/`action_back_draft()`. `action_confirm()` ALSO sets `intake_status='processed'` on any linked patient with `source='web_intake'` + `pending_review` — closes the intake queue loop.
- **Patient form**: header button **"Clinical Finding"** → `action_new_clinical_finding()` (window action, `default_patient_id` context) + a **Clinical Findings** notebook page with the `clinical_finding_ids` One2many.
- **`dental.visit` additions**: `referral_reason` (Char) + `dentist_signature` (Binary, `widget="signature"`).
- **Menu**: Dental > Clinical Findings (`action_dental_clinical_finding`), search groups by date/dentist/state + filters Draft/Completed, Gingivitis-Periodontitis, With Caries.
- **DOH Form 2 wiring** (`report/oral_health_report.py` `_fill_sheet`): the **latest completed** (`state='done'`) finding per patient augments `patient_conditions` → `teeth_with_caries` adds `D`, `gingivitis_periodontitis` adds `Gi`+`PD`, `oral_debris_calculus` adds `OD`+`Ca`, `dento_facial_anomaly` adds `DFA`. These feed report rows 30–35 (dental caries / gingivitis / periodontal / oral debris / calculus / dento-facial). Draft findings are ignored.
- **ACL**: Manager full, Assistant read/write/create (no unlink) — same pattern as other `dental.*` models.
- **Test record** (left for inspection): clinical finding id 2 (completed) + visit 767 on **Test Del Mundo** (PAT/2026/00410).

## Public Patient Intake (Phase 1+2 — Completed)

- **Route** `/patient-intake` (`GET`+`POST`, `auth='public'`, `website=True`) in `controllers/intake.py` (`DentalPatientIntake`). 5-step wizard template `views/patient_intake_templates.xml` + `static/src/js/patient_intake.js`.
  - **Steps**: 1 Personal → 2 Dental History → 3 Medical History → 4 Allergies & Conditions → 5 Consent & Waiver. Stepper displays indicator dots; Next/Back buttons; Enter-on-input advances (Crash-free on last step = submit).
- **Creates on submit** (ALL via `sudo()` — public user has zero ACL): `dental.patient` (`source='web_intake'`, `intake_status='pending_review'`, program flags 4Ps/IP/senior/PWD/solo-parent, dental-history fields) → `dental.medical.history` (DOH booleans from the `_CONDITION_OPTIONS` mapping in the controller; unmapped conditions → `medical_conditions` text; allergies → `allergies` text) → two `dental.consent` (`data_privacy` + `waiver`, `state='signed'`, `signed_by`/`signature` from canvas dataURL) → best-effort `_create_customer_partner()` to link `res.partner`.
- **Signature pads**: full-width `<canvas>` scaled to backing size by JS; pointer events → hidden `data-sig-input` field holds `data:image/png;base64,...`. Server `_valid_signature()` strips the dataURL prefix, caps 500 KB, verifies base64.
- **Validation / security**: honeypot `website` field (any value → silent thanks page), manual regex checks (phone/email/date), dependent-field notes required when a "Yes" flag is ticked, duplicate detection on `last_name`+`first_name`+`birthdate` (rejects with the existing record number), standard CSRF token.
- **CRITICAL form-validation gotcha (fixed Sep 2026)**: plain `form.checkValidity()`/`form.reportValidity()` in the Next handler fails in Chrome because hidden (`display:none`) `required` fields in inactive steps are still validated → console `An invalid form control ... is not focusable` and Next is blocked. Fix pattern used:
  - Server: inactive `<fieldset>`s get `t-att-disabled="'1' if N != active_step else None"` — **disabled** controls are exempt from constraint validation.
  - JS: `show(i)` toggles `step.disabled = (j !== index)`; `initStepper` bootstraps `index` from the fieldset that already has class `active` (so error re-render resumes on the offending step, not step 1).
  - Submit handler: validate ONLY `steps[index]` (`activeStep.checkValidity()/reportValidity()` — always visible/focusable), then re-enable ALL fieldsets (`step.disabled = false`) immediately before `form.submit()` so every field still POSTs.
- **Test procedure shipped with milestone**: submit the form twice (once intentional duplicate) to verify the Pending Review queue in **Dental > Web Intake Requests**, signatures visible on the patient's Consents page, `Mark Processed` button, and the DOH report picking up the intake data.
