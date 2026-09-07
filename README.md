# OBBS Dental Management System

A comprehensive **Dental Practice Management System** built on **Odoo 19 Community Edition**, designed to replace paper-based patient records with a modern, tablet-optimized Electronic Dental Record (EDR).

The primary objective of this project is to eliminate manual data entry by allowing receptionists, dental assistants, and dentists to capture patient information directly on a tablet in real time while maintaining a complete digital record of every patient.

---

# Objectives

- Eliminate handwritten patient records
- Digitize patient intake and consent forms
- Provide an interactive dental chart (odontogram)
- Maintain complete patient history
- Integrate appointments, billing, and inventory
- Support electronic signatures
- Optimize workflows for touch-enabled tablets

---

# Technology Stack

- **Framework:** Odoo 19 Community
- **Database:** PostgreSQL
- **Frontend:** Odoo OWL Framework
- **Backend:** Python
- **Database ORM:** Odoo ORM
- **Reports:** QWeb
- **Storage:** Persistent Docker Volume

---

# Module Name

```
obbs_dental
```

---

# Initial Module Structure

```
obbs_dental/
├── __init__.py
├── __manifest__.py
├── controllers/
│   ├── intake.py            # public 5-step web intake form (/patient-intake)
│   ├── portal.py            # patient portal: /my/patient, medical/dental history, chart
│   └── chart_geometry.py    # shared odontogram geometry (SVG mirror of the OWL widget)
├── models/
│   ├── dental_patient.py
│   ├── dental_medical_history.py
│   ├── dental_tooth.py
│   ├── dental_tooth_surface.py
│   ├── dental_condition.py
│   ├── dental_consent.py
│   ├── dental_history.py
│   ├── dental_service.py
│   ├── dental_visit.py
│   └── dental_clinical_finding.py
├── views/
│   ├── dental_patient_views.xml
│   ├── dental_medical_history_views.xml
│   ├── dental_visit_views.xml
│   ├── dental_history_views.xml
│   ├── dental_consent_views.xml
│   ├── dental_tooth_views.xml
│   ├── dental_condition_views.xml
│   ├── dental_service_views.xml
│   ├── dental_clinical_finding_views.xml
│   ├── patient_intake_templates.xml
│   ├── portal_patient_templates.xml
│   └── menus.xml
├── security/
│   ├── ir.model.access.csv
│   └── security.xml
├── data/
│   ├── sequence_data.xml
│   ├── dental_condition_data.xml
│   └── dental_service_data.xml
├── demo/
│   └── demo_data.py
├── report/
│   ├── __init__.py
│   ├── oral_health_wizard.py
│   ├── oral_health_wizard_views.xml
│   └── oral_health_report.py
├── static/
│   └── src/
│       ├── js/
│       │   ├── odontogram.js
│       │   ├── tooth_layout.js
│       │   ├── tooth_dialog.js
│       │   └── patient_intake.js
│       ├── xml/
│       │   ├── odontogram.xml
│       │   └── tooth_dialog.xml
│       └── scss/
└── ANGONO 2026 blank form 2.xlsx
```

---

# Core Models

## dental.patient

Stores the master patient profile.

Initially, this will be a standalone model linked to `res.partner` rather than inheriting it directly.

### Fields

- Patient Number
- Contact (`res.partner`)
- Last Name
- First Name
- Middle Name
- Birthdate
- Age (computed)
- Sex
- Blood Type
- Nationality
- Religion
- Occupation
- Home Address
- Mobile Number
- Email Address
- Dental Insurance
- Guardian
- Emergency Contact
- Active Status

---

## dental.visit

Represents every patient consultation / treatment-log entry (the DOH Individual Treatment Record log).

### Fields

- Patient
- Dentist
- Visit Date
- Services Rendered (M2M `dental.service`)
- Referred (+ Referral Reason)
- Counseling/Education
- Toothbrushing Drill (Under-6)
- OFC Upon Oral Exam / Complete Oral Rehabilitation
- Notes
- Dentist Signature

---

## dental.clinical.finding

Captures the clinician-written sections of the DOH Individual Patient Treatment Record — one row per dentist screening/consultation.

- A.1–A.5 Clinical Findings: periodontal disease (affected teeth + mobility I–III), torus palatinus/mandibularis, epulis/cyst/tumor, prosthesis (CD/RPD/FPD × upper/lower + years in use), ridge height
- B.1–B.4 Treatment Plan: root planing & scaling, extraction, surgical removal/biopsy, prosthesis repair/replacement
- Oral Health Status: caries count, oral debris/calculus, gingivitis/periodontitis, dento-facial anomaly, soft tissue lesions, permanent/deciduous teeth present, oro-facial anomaly (+ type), oral lesions (+ type), assessed by + position
- Clinical Notes + X-ray/Photo attachments
- Workflow state: Draft / Completed

---

## dental.medical.history

Stores the patient's complete medical and dental history.

Examples include:

- General Health
- Current Medication
- Previous Surgeries
- Hospitalization
- Smoking
- Alcohol Use
- Pregnancy
- Allergies
- Medical Conditions

Medical history should be versioned so historical changes are preserved instead of overwritten.

---

## dental.tooth

Stores the digital odontogram.

Each record represents a single tooth.

Example:

| Patient | Tooth | Condition | Treatment |
|----------|--------|-----------|-----------|
| John Doe | 11 | Caries | Composite Filling |
| John Doe | 26 | Missing | Implant |
| John Doe | 36 | Crown | Crown |

This normalized structure allows unlimited dental history while supporting an interactive graphical dental chart.

---

# Tablet-Optimized Interface

The application will be designed primarily for Android and iPad tablets using Odoo's OWL frontend.

Features include:

- Large touch-friendly controls
- Multi-step patient intake wizard
- Toggle switches
- Dropdown selections
- Date pickers
- Signature capture
- Camera integration
- Interactive odontogram
- Minimal keyboard usage

The objective is to make patient registration significantly faster than completing paper forms.

---

# Electronic Signature

Patients will digitally sign consent forms directly on the tablet.

Odoo's binary/image fields will store signatures that can be embedded into reports and printed forms.

---

# Planned Features

## Patient Management

- Patient Registration
- Medical History
- Dental History
- Emergency Contacts
- Insurance Information

---

## Clinical Records

- Consultation Records
- Diagnosis
- Clinical Notes
- Progress Notes
- Treatment Plans

---

## Interactive Odontogram

- Tooth Selection
- Tooth Conditions
- Existing Restorations
- Planned Procedures
- Completed Procedures
- Color-coded Visualization

---

## Attachments

Support for attaching:

- X-rays
- Clinical Photos
- Laboratory Results
- Referral Documents
- Insurance Documents

---

## Scheduling

- Appointment Calendar
- Dentist Schedule
- SMS Reminder
- Email Reminder

---

## Billing

Integration with Odoo Accounting.

Features include:

- Treatment Charges
- Payments
- Outstanding Balances
- Official Receipts
- Invoices

---

## Inventory

Integration with Odoo Inventory.

Track:

- Dental Materials
- Consumables
- Medicines
- Instruments

---

## Reports

- Patient History
- Daily Consultations
- Treatment Summary
- Income Reports
- Outstanding Balances
- Dentist Productivity

---

# Future Integrations

The module is designed to integrate seamlessly with existing Odoo applications.

- Calendar
- Contacts
- Accounting
- Inventory
- CRM
- Email
- SMS
- Documents
- Website Portal

---

# Development Roadmap — Status

## Milestone 1 — Foundation ✅ *(Completed)*

- [x] Create `obbs_dental`
- [x] Module manifest
- [x] Security groups
- [x] Menus
- [x] Patient model
- [x] Patient numbering
- [x] Basic list and form views

---

## Milestone 2 — Digital Patient Intake ✅ *(Completed)*

- [x] Patient Information
- [x] Medical History (versioned)
- [x] Dental History (tooth-level records with auto-computed arch/quadrant)
- [x] Consent Forms
- [x] Electronic Signature

---

## Milestone 3 — Interactive Odontogram ✅ *(Completed — V2 Surface-Based)*

- [x] OWL Dental Chart (surface-based circular odontogram)
- [x] Five independent surfaces per tooth — Center circle + 4 arc quadrants (Top/Bottom/Left/Right)
- [x] Surface-specific condition, treatment, and notes
- [x] Complete FDI notation (11–48 permanent + 51–85 pediatric) — 52 teeth
- [x] Modular architecture: `odontogram.js`, `tooth_layout.js`, `tooth_dialog.js`
- [x] `dental.tooth` + `dental.tooth.surface` normalized data model
- [x] Surface-specific color coding and click-to-edit dialog
- [x] Immediate Dental History tab refresh after save (no page reload required)
- [x] Circular 90° quadrant arcs with distinct stroke outlines

### Dental Condition Management ✅ *(Added in 1.1.0)*

- [x] Conditions moved from a hardcoded Selection to a `dental.condition` model (admin-managed)
- [x] Admin-managed color per condition (colored options in the chart dialog + legend)
- [x] `apply_to_whole_tooth` flag — 7 conditions (Rf, PR, Po, MO, M, JC, Imp) apply to all 5 surfaces
- [x] Whole-tooth conditions propagate treatment and notes to all surfaces
- [x] Surface-specific conditions are blocked when a whole-tooth condition exists (ValidationError)
- [x] Dental → Conditions menu with color widget and whole-tooth toggle
- [x] Data migration (1.1.0) converts existing surface records to the new model
- [x] Delete button in the Dental History tab (Manager group only)

---

## Milestone 4 — Clinical Workflow ✅ *(Completed)*

- [x] `dental.clinical.finding` model mirroring DOH Individual Treatment Record sections
- [x] A.1–A.5 clinical findings (periodontal disease + mobility, torus, epulis/cyst/tumor, prosthesis, ridge height)
- [x] B.1–B.4 treatment planning (root planing & scaling, extraction, surgical removal/biopsy, prosthesis repair/replacement)
- [x] Oral Health Status indicators + assessed-by fields
- [x] Clinical Notes + X-ray/Clinical Photo attachments (`many2many_binary`)
- [x] Draft → Completed workflow (Confirm also closes a pending web-intake queue entry)
- [x] Patient form: "Clinical Finding" header button + Clinical Findings notebook page
- [x] Dental → Clinical Findings menu with filters/groups
- [x] `dental.visit` gains Referral Reason + Dentist Signature
- [x] Completed findings feed DOH Form 2 report rows 30–35

---

## Public Patient Intake ✅ *(Completed)*

- [x] Public 5-step web wizard at `/patient-intake` (`auth='public'`, website)
- [x] Steps: Personal, Dental History, Medical History, Allergies & Conditions, Consent & Waiver
- [x] On-submit creates patient (`source='web_intake'`, `pending_review`) + medical history + Data Privacy consent + Extraction waiver (canvas signatures)
- [x] Best-effort `res.partner` auto-link for later portal access
- [x] Honeypot + CSRF + regex validation + duplicate detection
- [x] Dental > Web Intake Requests queue with Mark Processed / Reopen
- [x] Bug fix: inactive wizard steps are `disabled` server-side so hidden `required` fields never block validation (Chrome "not focusable" fix)

---

## Milestone 5a — Demo Data & DOH Reporting ✅ *(Completed)*

- [x] 100 realistic demo patients (Filipino names, Angono Rizal addresses, all age groups)
- [x] Medical histories with DOH boolean fields (hypertension, diabetes, etc.)
- [x] Dental conditions with 5 new DOH conditions (Gi, PD, OD, Ca, DFA)
- [x] `dental.service` lookup table (10 services)
- [x] `dental.visit` model with services M2M + DOH flags
- [x] DOH Oral Health Form 2 spreadsheet report (openpyxl)
- [x] Report wizard (monthly/quarterly/annual)
- [x] Menu: Dental > Reports > Oral Health Form 2

---

## Milestone 5b — Patient Portal ✅ *(Completed, Phases 1-5)*

- Portal test account: `deleon.jose@yahoo.com` / `Portal@123` → patient **PAT/2026/00310 Jose Gonzales De Leon** (the demo patient with a linked partner; the only one the portal can find). portal users have **zero ACL** on `dental.*` — every portal controller `sudo()`s and filters `[('partner_id','=',user.partner_id.id)]`.
- **Portal home cards** currently use the **same placeholder icon** (`/portal/static/src/img/portal-addresses.svg`, the core portal "Addresses" icon) on all four dental cards so the layout matches stock core cards. **Replace these with dental-specific SVG icons** (e.g. tooth chart, clipboard, calendar) via the `t-set="icon"` values in `views/portal_patient_templates.xml` — drop the SVGs in `static/src/img/` and reference them by module path.

### Phase 1 — Login Credentials & Account ☑️ *(Done)*
- [x] Linked `res.partner` on the patient from whom login credentials are derived
- [x] Invite button (Manager group) on the patient form
- [x] Email invite with a signup link + reset-password template

### Phase 2 — Patient Overview Page ☑️ *(Done)*
- [x] Custom portal controller (`CustomerPortal` subclass)
- [x] `/my/patient` overview route (personal, contact, insurance, emergency info)
- [x] "My Dental Records" card on the portal home (`/my`)

### Phase 3 — Medical History View ☑️ *(Done)*
- [x] `/my/medical_history` route + page
- [x] Accordion per medical history record with red/grey health-indicator badges
- [x] "My Medical History" card on the portal home

### Phase 4 — Dental History / Visits View ☑️ *(Done)*
- [x] `/my/dental_history` route + page
- [x] Visits accordion with services + DOH indicator badges
- [x] Dental Treatment Records table with condition color badges (from `dental.condition`)
- [x] "My Dental History" card on the portal home
- [x] Demo data now generates `dental.history` records (1-4 per ~30% of patients)

### Phase 5 — Dental Chart Read-Only View ☑️ *(Done)*
- [x] `/my/dental_chart` route + page
- [x] Read-only SVG odontogram (52 FDI teeth, 5 surfaces each) matching the backend widget
- [x] Condition color legend built from `dental.tooth.surface` latest records
- [x] "My Dental Chart" card on the portal home
- [x] Geometry ported to `controllers/chart_geometry.py` (tooth_layout.js)
- [x] Verified live: `/my/dental_chart` → 200, 52 tooth groups, 260 surface paths, legend matches backend chart colors

### Latest Updates (Sep 2026)
- Portal home cards: all four dental cards now render with the stock portal card layout + a shared placeholder icon (see note above).
- Phase 5 QWeb fixes: dict values must use `['key']` subscripts (`chart.key` raises `AttributeError`), and transform strings must be precomputed in Python (QWeb cannot concat `str + int`).

---

## Next Steps

1. **Milestone 5 — Operations** ⏳: Appointment scheduling, billing, payments, reports, dashboard, analytics.
2. **Replace placeholder portal card icons** with dental-specific SVGs (see note in Milestone 5b).
3. Add portal **attachment/viewing** (X-rays, clinical photos) and **consent form** display now that the Clinical Workflow milestone has landed.

---

## Milestone 5 — Operations ⏳ *(Pending)*

- [ ] Appointment Scheduling
- [ ] Billing
- [ ] Payment Recording
- [ ] Reports
- [ ] Dashboard
- [ ] Analytics

---

# Long-Term Vision

The long-term objective is to develop **OBBS Dental Management System** into a complete, enterprise-grade Dental Practice Management solution built on Odoo.

The system should support:

- Single Clinic Deployment
- Multi-Branch Clinics
- Cloud Deployment
- Tablet-Based Patient Intake
- Electronic Dental Records (EDR)
- Digital Consent Forms
- Interactive Odontogram
- Billing and Accounting
- Inventory Management
- Appointment Scheduling
- Reporting and Analytics

By leveraging Odoo's robust ecosystem, the platform will provide a scalable, modular, and fully integrated solution that modernizes dental clinic operations while eliminating paper-based workflows.