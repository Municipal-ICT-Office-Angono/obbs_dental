import random
import math
import re
from datetime import date, timedelta
from odoo import api, models

EMAIL_DOMAINS = ['gmail.com', 'yahoo.com', 'outlook.com', 'yahoo.com.ph', 'hotmail.com']


def _slugify(name):
    return re.sub(r'[^a-zA-Z0-9]', '', name).lower()

FIRST_NAMES_MALE = [
    'Juan', 'Jose', 'Pedro', 'Antonio', 'Manuel', 'Francisco', 'Ricardo',
    'Fernando', 'Ramon', 'Eduardo', 'Roberto', 'Carlos', 'Miguel', 'Luis',
    'Alejandro', 'Andres', 'Mariano', 'Rafael', 'Arturo', 'Victor',
    'Daniel', 'Patrick', 'Mark', 'John', 'Michael', 'James', 'Robert',
    'David', 'Joseph', 'Thomas', 'Christopher', 'Daniel', 'Matthew',
    'Anthony', 'Andrew', 'Joshua', 'Nathan', 'Kyle', 'Ryan', 'Jay',
    'Rey', 'Jerome', 'Marvin', 'Cristian', 'Angelo', 'Vince', 'Dennis',
    'Joel', 'Benedict', 'Alvin', 'Bernard',
]

FIRST_NAMES_FEMALE = [
    'Maria', 'Ana', 'Rosa', 'Teresa', 'Luz', 'Corazon', 'Elena',
    'Carmen', 'Rosario', 'Lourdes', 'Guadalupe', 'Milagros', 'Esperanza',
    'Beatriz', 'Virginia', 'Gloria', 'Grace', 'Joy', 'Rose', 'May',
    'Anna', 'Christine', 'Jessica', 'Nicole', 'Patricia', 'Angelica',
    'Maria', 'Samantha', 'Kayla', 'Princess', 'Jasmine', 'Hannah',
    'Andrea', 'Stephanie', 'Frances', 'Catherine', 'Liza', 'Mia',
    'Sofia', 'Isabella', 'Chloe', 'Zoe', 'Alyssa', 'Danielle',
    'Mariane', 'Jessa', 'Crizza', 'Rina', 'Lorna', 'Vilma',
]

MIDDLE_NAMES = [
    'Santos', 'Cruz', 'Reyes', 'Garcia', 'Mendoza', 'Torres', 'Ramos',
    'Rivera', 'Gonzales', 'Aquino', 'Dela Cruz', 'Dela Rosa', 'Villanueva',
    'Bautista', 'Mercado', 'Castillo', 'Fernandez', 'Lopez', 'Perez',
    'Santiago', 'Martinez', 'Rodriguez', 'Hernandez', 'Morales', 'Diaz',
    'Moreno', 'Romero', 'Gutierrez', 'Ortiz', 'Gomez', 'Ruiz',
]

LAST_NAMES = [
    'Dela Rosa', 'Villanueva', 'Aquino', 'Bautista', 'Mercado', 'Castillo',
    'Fernandez', 'Lopez', 'Perez', 'Santiago', 'Martinez', 'Rodriguez',
    'Hernandez', 'Morales', 'Diaz', 'Moreno', 'Romero', 'Gutierrez',
    'Ortiz', 'Gomez', 'Ruiz', 'Alvarez', 'Navarro', 'Medina',
    'Santos', 'Cruz', 'Reyes', 'Garcia', 'Mendoza', 'Torres',
    'Ramos', 'Rivera', 'Gonzales', 'Dela Cruz', 'Dela Rosa',
    'Soriano', 'Valdez', 'Salazar', 'Pascual', 'Manalo', 'Tolentino',
    'Rivero', 'Enriquez', 'Padilla', 'Aguilar', 'Jimenez', 'Aguilar',
    'De Leon', 'Tan', 'Ong', 'Lim', 'Chua', 'Sy',
]

BARANGAYS = [
    'San Isidro', 'San Roque', 'San Miguel', 'Mahabang Parang',
    'Poblacion', 'Kalayaan', 'Bagumbayan', 'San Juan',
    'San Vicente', 'Santo Nino', 'San Andres', 'San Carlos',
    'Santa Cruz', 'San Nicolas', 'San Pedro', 'San Pablo',
    'San Lorenzo', 'San Gabriel', 'San Agustin', 'San Sebastian',
]

OCCUPATIONS = [
    'Teacher', 'Nurse', 'Engineer', 'Accountant', 'Driver', 'Vendor',
    'Farmer', 'Construction Worker', 'Housewife', 'Student', 'OFW',
    'Government Employee', 'Business Owner', 'Mechanic', 'Electrician',
    'Plumber', 'Carpenter', 'Security Guard', 'Clerk', 'Salesperson',
    'Customer Service', 'IT Professional', 'Architect', 'Lawyer',
    'Doctor', 'Pharmacist', 'Dentist', 'Technician', 'Chef', 'Baker',
    'Seaman', 'Call Center Agent', 'Freelancer', 'Retired', 'Unemployed',
]

ALLERGIES_LIST = [
    'Penicillin', 'Sulfa drugs', 'Latex', 'NSAIDs (Ibuprofen)',
    'Local anesthetics (Lidocaine)', 'Aspirin', 'Codeine', 'Cephalosporins',
    'Nickel (metal)', 'Acrylic', 'None known',
]

MEDICAL_CONDITIONS_TEXT = [
    'Hypertension, maintained on Amlodipine 5mg daily',
    'Type 2 Diabetes Mellitus, Metformin 500mg BID',
    'Hypertension and Type 2 DM, maintenance medications',
    'Asthma, uses Salbutamol inhaler as needed',
    'Hypothyroidism, Levothyroxine 50mcg daily',
    'Bronchial Asthma since childhood',
    'Hepatitis B carrier',
    'History of stroke (CVA) 2020, residual left-sided weakness',
    'Rheumatic heart disease, prophylactic Penicillin',
    'Chronic Kidney Disease Stage 3, dialysis twice weekly',
    'Breast cancer survivor, post-mastectomy 2023',
    'Lung cancer, under chemotherapy',
    'Anemia (Iron Deficiency), Ferrous Sulfate 325mg TID',
    'Hyperthyroidism, Methimazole 10mg daily',
    'No significant medical history',
    'Well-controlled asthma',
    'Mild hypertension, lifestyle modification only',
    'History of appendectomy 2018',
    'Cholecystectomy 2019',
    'Cesarean section 2022',
]

MEDICATIONS = [
    'Amlodipine 5mg', 'Metformin 500mg', 'Losartan 50mg',
    'Omeprazole 20mg', 'Levothyroxine 50mcg', 'Salbutamol inhaler',
    'Ferrous Sulfate 325mg', 'Methimazole 10mg', 'Aspirin 81mg',
    'Atorvastatin 20mg', 'Metoprolol 50mg', 'None',
    'Maintenance: Amlodipine + Metformin', 'None reported',
    'Multivitamins', 'Calcium supplements', 'None',
]

SURGERIES = [
    'Appendectomy (2018)', 'Cholecystectomy (2019)',
    'Cesarean Section (2022)', 'Tonsillectomy (2015)',
    'Hernia repair (2020)', 'None reported',
    'Knee arthroscopy (2021)', 'None', 'Circumcision (childhood)',
    'None reported',
]

HOSPITALIZATIONS = [
    'None reported', 'Confined at Amang Rodriguez Memorial Medical Center (2020) for pneumonia',
    'Confined at Manila Doctors Hospital (2019) for cholecystectomy',
    'Confined at East Avenue Medical Center (2022) for delivery',
    'None', 'Confined at Provincial Hospital (2021) for dengue',
    'None reported', 'ICU admission 2020 for CVA',
]

HEALTH_NOTES = [
    'Generally in good health', 'No known systemic disease',
    'Well-nourished, well-hydrated', 'Alert and cooperative',
    'Blood pressure within normal limits', 'Chief complaint: toothache',
    'Routine dental checkup', 'Referral for dental extraction',
    'Follow-up for dental restoration', 'Emergency: dental abscess',
    'Prenatal dental checkup', 'Post-extraction follow-up',
]

TREATMENT_NOTES = [
    'Oral prophylaxis completed', 'Composite restoration done',
    'Extraction of tooth #36', 'Temporary filling placed',
    'Sealant applied to tooth #16', 'Root canal treatment referred',
    'Gum treatment - scaling and root planing', 'Fluoride varnish applied',
    'Counseling on oral hygiene and diet', 'Referral to specialist',
    'Post-extraction instructions given', 'Crown preparation done',
    'Abscess incision and drainage', 'Extraction done, no complications',
    'Filling completed, patient tolerated procedure well',
]

CONSENT_DESCRIPTIONS = [
    'General consent for dental treatment',
    'Consent for dental extraction under local anesthesia',
    'Consent for dental implant placement',
    'Consent for orthodontic treatment',
    'Consent for dental X-ray exposure',
    'Consent for clinical photography',
    'Consent for root canal treatment',
    'Consent for general anesthesia for dental surgery',
]

PHYSICAL_ADDRESSES = [
    'Brgy. {brgy}, Angono, Rizal',
    'Sitio {sitio}, Brgy. {brgy}, Angono, Rizal',
    '#{{{num}}}, Brgy. {brgy}, Angono, Rizal',
    'Purok {purok}, Brgy. {brgy}, Angono, Rizal',
]

SITIOS = ['Lambingan', 'Malakaban', 'Pook', 'Tabon', 'Looban', 'Kuylayan']
PUROKS = ['Sampaguita', 'Rose', 'Orchid', 'Jasmine', 'Gumamela', 'Santan']
BRGY_NUMS = list(range(1, 20))


class DentalPatient(models.Model):
    _inherit = 'dental.patient'

    @api.model
    def demo_generate(self):
        conditions = self.env['dental.condition'].search([])
        cond_map = {}
        for c in conditions:
            cond_map[c.code] = c.id

        services = self.env['dental.service'].search([])
        svc_map = {}
        for s in services:
            svc_map[s.code] = s.id

        patients = self._create_demo_patients()
        self._create_demo_medical_histories(patients)
        self._create_demo_dental_conditions(patients, cond_map)
        self._create_demo_visits(patients, svc_map)
        self._create_demo_dental_history(patients, cond_map)
        self._create_demo_consents(patients)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Demo Data Generated',
                'message': f'Successfully created {len(patients)} patients with medical histories, dental conditions, visits, and consents.',
                'type': 'success',
                'sticky': False,
            }
        }

    def _create_demo_patients(self):
        patients = self.env['dental.patient']
        rng = random.Random(42)

        age_distribution = [
            (0, 0, 5),
            (1, 4, 10),
            (5, 9, 15),
            (10, 14, 12),
            (15, 19, 10),
            (20, 59, 38),
            (60, 85, 10),
        ]

        today = date.today()
        all_names_used = set()
        all_emails_used = set()

        for age_min, age_max, count in age_distribution:
            for _ in range(count):
                sex = rng.choice(['male', 'female'])

                while True:
                    fn = rng.choice(FIRST_NAMES_MALE if sex == 'male' else FIRST_NAMES_FEMALE)
                    ln = rng.choice(LAST_NAMES)
                    mn = rng.choice(MIDDLE_NAMES)
                    key = (fn, mn, ln)
                    if key not in all_names_used:
                        all_names_used.add(key)
                        break

                f_slug = _slugify(fn)
                l_slug = _slugify(ln)
                m_slug = _slugify(mn)
                while True:
                    fmt = rng.randrange(4)
                    if fmt == 0:
                        email = f'{f_slug}.{l_slug}'
                    elif fmt == 1:
                        email = f'{l_slug}.{f_slug}'
                    elif fmt == 2:
                        email = f'{f_slug}{l_slug[0]}{m_slug[0]}'
                    else:
                        email = f'{f_slug}_{l_slug}'
                    email = f'{email}{rng.randrange(2) and chr(97 + rng.randrange(26)) or ""}@{rng.choice(EMAIL_DOMAINS)}'
                    if email not in all_emails_used:
                        all_emails_used.add(email)
                        break

                age = rng.randint(age_min, age_max)
                birthdate = today - timedelta(days=age * 365 + rng.randint(0, 364))

                brgy = rng.choice(BARANGAYS)
                address_tmpl = rng.choice(PHYSICAL_ADDRESSES)
                address = address_tmpl.format(
                    brgy=brgy,
                    sitio=rng.choice(SITIOS),
                    purok=rng.choice(PUROKS),
                    num=rng.randint(1, 150),
                )

                mobile = f'09{rng.randint(100000000, 999999999)}'
                blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
                blood_type = rng.choice(blood_types)
                religions = ['Roman Catholic', 'Iglesia ni Cristo', 'Protestant', 'Islam', 'Buddhist']
                religion = rng.choice(religions) if rng.random() > 0.1 else 'Roman Catholic'

                occupation = rng.choice(OCCUPATIONS)
                if age < 6:
                    occupation = 'Child'
                elif age < 18:
                    occupation = 'Student'

                insurance_options = ['PhilHealth', 'Maxicare', 'Medicard', 'None', 'None', 'None']
                insurance = rng.choice(insurance_options)

                patient = self.create({
                    'first_name': fn,
                    'middle_name': mn,
                    'last_name': ln,
                    'birthdate': birthdate,
                    'sex': sex,
                    'blood_type': blood_type,
                    'nationality': 'Filipino',
                    'religion': religion,
                    'occupation': occupation,
                    'home_address': address,
                    'barangay': brgy,
                    'mobile': mobile,
                    'email': email,
                    'dental_insurance': insurance if insurance != 'None' else False,
                })
                patients |= patient

        return patients

    def _create_demo_medical_histories(self, patients):
        med_env = self.env['dental.medical.history']
        rng = random.Random(42)

        for patient in patients:
            age = patient.age
            sex = patient.sex

            has_hypertension = rng.random() < (0.35 if age >= 50 else 0.10 if age >= 30 else 0.02)
            has_diabetes = rng.random() < (0.20 if age >= 50 else 0.05 if age >= 30 else 0.01)
            has_cardio = rng.random() < (0.15 if age >= 50 else 0.03)
            has_thyroid = rng.random() < 0.04
            has_hepatitis = rng.random() < 0.03
            has_malignancy = rng.random() < 0.03
            has_blood_disorders = rng.random() < 0.04
            has_hospitalization = rng.random() < 0.12
            has_blood_transfusion = rng.random() < 0.04
            has_tattoo = rng.random() < (0.08 if sex == 'male' else 0.03)
            has_smoking = rng.random() < (0.30 if sex == 'male' and age >= 15 else 0.05 if sex == 'female' and age >= 15 else 0.0)
            has_alcohol = rng.random() < (0.25 if sex == 'male' and age >= 15 else 0.08 if sex == 'female' and age >= 15 else 0.0)
            has_betel_nut = rng.random() < 0.04
            is_pregnant = (sex == 'female' and 15 <= age <= 49 and rng.random() < 0.12)
            has_bruxism = rng.random() < 0.10

            conditions_text = []
            if has_hypertension:
                conditions_text.append('Hypertension')
            if has_diabetes:
                conditions_text.append('Diabetes Mellitus')
            if has_cardio:
                conditions_text.append('Cardiovascular disease')
            if has_thyroid:
                conditions_text.append('Thyroid disorder')
            if has_hepatitis:
                conditions_text.append('Hepatitis B')
            if has_malignancy:
                conditions_text.append('Malignancy')
            if has_blood_disorders:
                conditions_text.append('Blood disorder (anemia)')

            allergies = rng.choice(ALLERGIES_LIST)
            if rng.random() < 0.6:
                allergies = 'None known'

            medication = rng.choice(MEDICATIONS)
            if not conditions_text:
                medication = 'None'

            surgery = rng.choice(SURGERIES)
            hospitalization = rng.choice(HOSPITALIZATIONS) if has_hospitalization else 'None reported'

            general_health = rng.choice([
                'Generally in good health',
                'No known systemic disease',
                'Well-nourished, well-hydrated',
                'Fair health, some chronic conditions',
                'Good overall health',
            ])

            month = rng.randint(1, 8)
            day = rng.randint(1, 28)
            visit_date = date(2026, month, day)

            med_env.create({
                'patient_id': patient.id,
                'date': visit_date,
                'general_health': general_health,
                'current_medication': medication,
                'previous_surgeries': surgery,
                'hospitalization': hospitalization,
                'smoking': has_smoking,
                'alcohol_use': has_alcohol,
                'pregnancy': is_pregnant,
                'bruxism': has_bruxism,
                'betel_nut': has_betel_nut,
                'tattoo': has_tattoo,
                'allergies': allergies,
                'medical_conditions': ', '.join(conditions_text) if conditions_text else 'None',
                'hypertension': has_hypertension,
                'diabetes': has_diabetes,
                'blood_disorders': has_blood_disorders,
                'cardiovascular': has_cardio,
                'thyroid_disorders': has_thyroid,
                'hepatitis': has_hepatitis,
                'malignancy': has_malignancy,
                'hospitalization_history': has_hospitalization,
                'blood_transfusion': has_blood_transfusion,
                'notes': rng.choice(HEALTH_NOTES),
            })

    def _create_demo_dental_conditions(self, patients, cond_map):
        tooth_env = self.env['dental.tooth']
        surface_env = self.env['dental.tooth.surface']
        rng = random.Random(42)

        permanent_teeth = [str(n) for n in range(11, 19)] + \
                          [str(n) for n in range(21, 29)] + \
                          [str(n) for n in range(31, 39)] + \
                          [str(n) for n in range(41, 49)]

        pediatric_teeth = [str(n) for n in range(51, 56)] + \
                          [str(n) for n in range(61, 66)] + \
                          [str(n) for n in range(71, 76)] + \
                          [str(n) for n in range(81, 86)]

        surfaces = ['T', 'B', 'L', 'R', 'C']

        condition_weights = [
            ('D', 35),
            ('Co', 15),
            ('Am', 10),
            ('PR', 15),
            ('M', 8),
            ('S', 4),
            ('X', 3),
            ('Gi', 3),
            ('Ca', 3),
            ('JC', 1),
            ('In', 1),
            ('Rf', 1),
            ('MO', 1),
        ]

        cond_codes = [c for c, w in condition_weights]
        cond_weights = [w for c, w in condition_weights]

        for patient in patients:
            age = patient.age

            if age < 6:
                available = pediatric_teeth
            elif age < 12:
                available = permanent_teeth + [t for t in pediatric_teeth if int(t) % 10 <= 5]
            else:
                available = permanent_teeth

            num_teeth_affected = rng.randint(2, min(10, len(available)))
            affected_teeth = rng.sample(available, num_teeth_affected)

            for tooth_num in affected_teeth:
                tooth = tooth_env.create({
                    'patient_id': patient.id,
                    'tooth_number': tooth_num,
                })

                is_whole_tooth_cond = rng.random() < 0.3
                if is_whole_tooth_cond:
                    code = rng.choices(
                        ['PR', 'M', 'MO', 'JC', 'Rf', 'DFA'],
                        weights=[20, 10, 3, 3, 2, 2],
                        k=1
                    )[0]
                    condition_id = cond_map.get(code)
                    if condition_id:
                        treatment = rng.choice(TREATMENT_NOTES) if code != 'PR' else ''
                        for surf in surfaces:
                            surface_env.create({
                                'tooth_id': tooth.id,
                                'surface': surf,
                                'condition': condition_id,
                                'treatment': treatment,
                                'notes': rng.choice(['', '', 'Routine observation']),
                                'date': date(2026, rng.randint(1, 8), rng.randint(1, 28)),
                            })
                else:
                    num_surfaces = rng.randint(1, 3)
                    affected_surfaces = rng.sample(surfaces, num_surfaces)
                    for surf in affected_surfaces:
                        code = rng.choices(cond_codes, weights=cond_weights, k=1)[0]
                        condition_id = cond_map.get(code)
                        if condition_id:
                            treatment = rng.choice(TREATMENT_NOTES) if code != 'PR' else ''
                            surface_env.create({
                                'tooth_id': tooth.id,
                                'surface': surf,
                                'condition': condition_id,
                                'treatment': treatment,
                                'notes': rng.choice(['', '', 'Patient informed', 'Follow-up needed']),
                                'date': date(2026, rng.randint(1, 8), rng.randint(1, 28)),
                            })

    def _create_demo_visits(self, patients, svc_map):
        visit_env = self.env['dental.visit']
        rng = random.Random(42)

        service_combos = [
            ([svc_map.get('SC')], False, True),
            ([svc_map.get('SC'), svc_map.get('PF')], False, True),
            ([svc_map.get('EX')], False, True),
            ([svc_map.get('SC'), svc_map.get('SE')], False, False),
            ([svc_map.get('PF')], False, True),
            ([svc_map.get('TF')], False, True),
            ([svc_map.get('SC'), svc_map.get('FT')], False, False),
            ([svc_map.get('GT')], False, True),
            ([svc_map.get('AD')], True, True),
            ([svc_map.get('SC'), svc_map.get('OS')], True, True),
            ([svc_map.get('EX'), svc_map.get('PO')], False, True),
            ([svc_map.get('SE'), svc_map.get('FT')], False, False),
        ]

        for patient in patients:
            num_visits = rng.choices([1, 2, 3], weights=[40, 35, 25], k=1)[0]

            for v in range(num_visits):
                month = rng.randint(1, 8)
                day = rng.randint(1, 28)
                visit_date = date(2026, month, day)

                services, referred, counseling = rng.choice(service_combos)
                services = [s for s in services if s]

                is_child = patient.age < 6
                toothbrush = is_child and rng.random() < 0.5
                ofc_exam = is_child and rng.random() < 0.4
                ofc_rehab = is_child and rng.random() < 0.1

                visit_env.create({
                    'patient_id': patient.id,
                    'visit_date': visit_date,
                    'service_ids': [(6, 0, services)],
                    'referred': referred,
                    'counseling': counseling,
                    'toothbrush_drill': toothbrush,
                    'ofc_oral_exam': ofc_exam,
                    'ofc_rehabilitation': ofc_rehab,
                    'notes': rng.choice(TREATMENT_NOTES),
                })

    def _create_demo_dental_history(self, patients, cond_map):
        history_env = self.env['dental.history']
        rng = random.Random(42)

        all_tooth_numbers = [
            '11', '12', '13', '14', '15', '16', '17', '18',
            '21', '22', '23', '24', '25', '26', '27', '28',
            '31', '32', '33', '34', '35', '36', '37', '38',
            '41', '42', '43', '44', '45', '46', '47', '48',
        ]
        treat_codes = ['PR', 'D', 'Am', 'Co', 'JC', 'S', 'X', 'XO', 'Rf', 'Im', 'Imp', 'Po', 'Rm', 'ABF', 'ABR']

        for patient in patients:
            if rng.random() > 0.7:
                continue
            visits = self.env['dental.visit'].search([('patient_id', '=', patient.id)])
            visit_dates = [v.visit_date for v in visits]
            num_entries = rng.randint(1, 4)
            used_teeth = set()
            for _ in range(num_entries):
                tooth = rng.choice([t for t in all_tooth_numbers if t not in used_teeth])
                used_teeth.add(tooth)
                code = rng.choice(treat_codes)
                entry_date = rng.choice(visit_dates) if visit_dates else date(2026, rng.randint(1, 8), rng.randint(1, 28))
                history_env.create({
                    'patient_id': patient.id,
                    'tooth_number': tooth,
                    'date': entry_date,
                    'condition': code,
                    'treatment': rng.choice(TREATMENT_NOTES) if code != 'PR' else '',
                    'notes': rng.choice(['', 'Routine treatment', 'Patient informed', 'Follow-up scheduled']),
                })

    def _create_demo_consents(self, patients):
        consent_env = self.env['dental.consent']
        rng = random.Random(42)

        consent_types = ['general', 'surgery', 'anesthesia', 'photo', 'xray', 'implant', 'ortho', 'other']

        for patient in patients:
            if rng.random() < 0.6:
                num_consents = rng.randint(1, 2)
                for _ in range(num_consents):
                    ctype = rng.choice(consent_types)
                    month = rng.randint(1, 8)
                    day = rng.randint(1, 28)
                    signed_date = date(2026, month, day)

                    consent_env.create({
                        'patient_id': patient.id,
                        'consent_type': ctype,
                        'description': rng.choice(CONSENT_DESCRIPTIONS),
                        'signed_date': signed_date,
                        'signed_by': patient.display_name,
                        'relationship': 'Self',
                        'state': 'signed',
                        'notes': rng.choice(['', 'Patient briefed on procedure', 'Informed consent obtained']),
                    })
