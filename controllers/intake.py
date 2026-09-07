import base64
import logging
import re
from datetime import datetime, date

from odoo import fields, http
from odoo.http import request

_logger = logging.getLogger(__name__)

_ALLERGY_LABELS = {
    'allergy_anesthetics': 'Local anesthetics',
    'allergy_penicillin': 'Penicillin / Antibiotics',
    'allergy_aspirin': 'Aspirin',
    'allergy_sulfa': 'Sulfa drugs',
    'allergy_latex': 'Latex',
}

_CONDITION_OPTIONS = {
    'cond_high_bp': ('hypertension', 'High blood pressure'),
    'cond_low_bp': (None, 'Low blood pressure'),
    'cond_diabetes': ('diabetes', 'Diabetes'),
    'cond_chest_pain': (None, 'Chest pain'),
    'cond_heart_disease': ('cardiovascular', 'Heart disease'),
    'cond_heart_attack': (None, 'Heart attack'),
    'cond_heart_murmur': (None, 'Heart murmur'),
    'cond_heart_surgery': (None, 'Heart surgery'),
    'cond_stroke': (None, 'Stroke'),
    'cond_respiratory': (None, 'Respiratory problem'),
    'cond_tb': (None, 'Tuberculosis'),
    'cond_kidney': (None, 'Kidney disease'),
    'cond_asthma': (None, 'Asthma'),
    'cond_thyroid': ('thyroid_disorders', 'Thyroid problem'),
    'cond_fainting': (None, 'Fainting / Seizure'),
    'cond_aids': (None, 'AIDS / HIV'),
    'cond_epilepsy': (None, 'Epilepsy / Convulsion'),
    'cond_hepatitis': ('hepatitis', 'Hepatitis / Liver disease'),
    'cond_stomach': (None, 'Stomach troubles / Ulcers'),
    'cond_cancer': ('malignancy', 'Cancer / Tumor'),
    'cond_arthritis': (None, 'Arthritis'),
}

_PHONE_RE = re.compile(r'^\+?[\d\s\-()]{7,20}$')
_EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


class DentalPatientIntake(http.Controller):

    _conditions = [{'key': k, 'label': label} for k, (_f, label) in _CONDITION_OPTIONS.items()]

    @http.route('/patient-intake', type='http', auth='public', website=True,
                methods=['GET', 'POST'])
    def patient_intake(self, **post):
        if request.httprequest.method == 'POST':
            return self._process_intake(post)
        return request.render('obbs_dental.patient_intake_page',
                              self._form_values({}))

    def _form_values(self, posted, errors=None, active_step=1):
        return {
            'posted': posted,
            'errors': errors or [],
            'active_step': active_step,
            '_CONDITIONS': self._conditions,
            'csrf_token': request.csrf_token(),
        }

    @staticmethod
    def _parse_date(value, label, step, errors, required=True):
        value = (value or '').strip()
        if not value:
            if required:
                errors.append({'step': step, 'msg': 'Your %s is required.' % label})
            return None
        try:
            return datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            errors.append({'step': step, 'msg': 'Enter a valid %s.' % label})
            return None

    @staticmethod
    def _valid_signature(value):
        if not value:
            return False
        value = value.strip()
        if not value:
            return False
        if ',' in value and value.split(',', 1)[0].startswith('data:image'):
            value = value.split(',', 1)[1]
        if len(value) > 500000:
            return False
        try:
            base64.b64decode(value, validate=True)
        except Exception:
            return False
        return value

    def _process_intake(self, post):
        posted = dict(post)
        errors = []

        if posted.get('website'):
            return request.render('obbs_dental.patient_intake_thanks',
                                  {'patient': None, 'posted': posted})

        last_name = (posted.get('last_name') or '').strip()
        first_name = (posted.get('first_name') or '').strip()
        middle_name = (posted.get('middle_name') or '').strip()
        sex = posted.get('sex')
        mobile = (posted.get('mobile') or '').strip()
        email = (posted.get('email') or '').strip()
        barangay = (posted.get('barangay') or '').strip()
        address = (posted.get('address') or '').strip()
        occupation = (posted.get('occupation') or '').strip()
        guardian = (posted.get('guardian') or '').strip()
        philhealth = (posted.get('philhealth_number') or '').strip()

        if not last_name:
            errors.append({'step': 1, 'msg': 'Your last name is required.'})
        if not first_name:
            errors.append({'step': 1, 'msg': 'Your first name is required.'})
        if sex not in ('male', 'female'):
            errors.append({'step': 1, 'msg': 'Please select your sex.'})
        birthdate = self._parse_date(posted.get('birthdate'), 'birth date', 1, errors)
        if not mobile:
            errors.append({'step': 1, 'msg': 'Your contact number is required.'})
        elif not _PHONE_RE.match(mobile):
            errors.append({'step': 1, 'msg': 'Enter a valid contact number.'})
        if email and not _EMAIL_RE.match(email):
            errors.append({'step': 1, 'msg': 'Enter a valid e-mail address.'})
        if not barangay:
            errors.append({'step': 1, 'msg': 'Your barangay is required.'})
        if not address:
            errors.append({'step': 1, 'msg': 'Your address is required.'})

        age = None
        if birthdate:
            today = date.today()
            age = today.year - birthdate.year - (
                (today.month, today.day) < (birthdate.month, birthdate.day))
            if age < 0:
                errors.append({'step': 1, 'msg': 'Birth date cannot be in the future.'})
            elif age < 18 and not guardian:
                errors.append({'step': 1, 'msg': 'A parent or guardian is required for minors under 18.'})

        last_dental_visit = self._parse_date(
            posted.get('last_dental_visit'), 'most recent dental visit', 2, errors,
            required=False)
        visit_frequency = posted.get('visit_frequency') or ''
        visit_frequency = (visit_frequency if visit_frequency in (
            'twice_year', 'once_year', 'never') else '')
        orthodontic_history = (posted.get('orthodontic_history') or '').strip()
        has_prosthesis = bool(posted.get('prosthesis'))
        prosthesis_since = (posted.get('prosthesis_since') or '').strip()
        referred_by = (posted.get('referred_by') or '').strip()
        referred_reason = (posted.get('referred_reason') or '').strip()

        under_treatment = bool(posted.get('under_treatment'))
        under_treatment_notes = (posted.get('under_treatment_notes') or '').strip()
        if under_treatment and not under_treatment_notes:
            errors.append({'step': 3, 'msg': 'Please describe the condition being treated.'})
        serious_illness = bool(posted.get('serious_illness'))
        serious_illness_notes = (posted.get('serious_illness_notes') or '').strip()
        if serious_illness and not serious_illness_notes:
            errors.append({'step': 3, 'msg': 'Please describe the illness or operation.'})
        was_hospitalized = bool(posted.get('was_hospitalized'))
        hospitalization_notes = (posted.get('hospitalized_notes') or '').strip()
        if was_hospitalized and not hospitalization_notes:
            errors.append({'step': 3, 'msg': 'Please state when and why you were hospitalized.'})
        taking_medication = bool(posted.get('taking_medication'))
        medication_notes = (posted.get('medication_notes') or '').strip()
        if taking_medication and not medication_notes:
            errors.append({'step': 3, 'msg': 'Please specify your current medications.'})

        allergy_labels = []
        for key, label in _ALLERGY_LABELS.items():
            if posted.get(key):
                allergy_labels.append(label)
        allergy_others = (posted.get('allergy_others') or '').strip()
        if allergy_others:
            allergy_labels.append(allergy_others)
        allergies = ', '.join(allergy_labels)

        pregnant = bool(posted.get('pregnant'))
        pregnancy_months = (posted.get('pregnancy_months') or '').strip()
        if pregnant and not pregnancy_months:
            pregnancy_months = '1-9'
        nursing = bool(posted.get('nursing'))
        birth_control = bool(posted.get('birth_control'))

        condition_bools = {}
        condition_labels = []
        for key, (field, label) in _CONDITION_OPTIONS.items():
            if posted.get(key):
                condition_labels.append(label)
                if field:
                    condition_bools[field] = True
        cond_others = (posted.get('cond_others') or '').strip()
        if cond_others:
            condition_labels.append('Others: %s' % cond_others)
        medical_conditions = ', '.join(condition_labels)

        consent_name = (posted.get('consent_name') or '').strip()
        waiver_name = (posted.get('waiver_name') or '').strip()
        consent_signature = self._valid_signature(posted.get('consent_signature'))
        waiver_signature = self._valid_signature(posted.get('waiver_signature'))

        if not posted.get('consent_agree'):
            errors.append({'step': 5, 'msg': 'You must agree to the Data Privacy Consent.'})
        if not consent_name:
            errors.append({'step': 5, 'msg': 'Enter your full name on the Data Privacy Consent.'})
        if not consent_signature:
            errors.append({'step': 5, 'msg': 'Please sign the Data Privacy Consent.'})
        if not posted.get('waiver_agree'):
            errors.append({'step': 5, 'msg': 'You must agree to the Waiver.'})
        if not waiver_name:
            errors.append({'step': 5, 'msg': 'Enter your full name on the Waiver.'})
        if not waiver_signature:
            errors.append({'step': 5, 'msg': 'Please sign the Waiver.'})

        if birthdate and last_name and first_name:
            duplicate = request.env['dental.patient'].sudo().search([
                ('last_name', '=ilike', last_name),
                ('first_name', '=ilike', first_name),
                ('birthdate', '=', birthdate),
            ], limit=1)
            if duplicate:
                errors.append({
                    'step': 1,
                    'msg': 'A patient with this name and birth date already exists '
                           '(Record %s). Please contact the clinic instead of filing '
                           'a new intake form.' % duplicate.patient_number,
                })

        if errors:
            active_step = min(e['step'] for e in errors)
            return request.render(
                'obbs_dental.patient_intake_page',
                self._form_values(posted, errors, active_step))

        patient = self._create_patient(
            posted, last_name, first_name, middle_name, sex, birthdate, mobile,
            email, barangay, address, occupation, guardian, philhealth,
            last_dental_visit, visit_frequency, orthodontic_history,
            has_prosthesis, prosthesis_since, referred_by, referred_reason)

        self._create_medical_history(
            patient, under_treatment, under_treatment_notes, serious_illness,
            serious_illness_notes, was_hospitalized, hospitalization_notes,
            taking_medication, medication_notes, posted, allergies, pregnant,
            pregnancy_months, nursing, birth_control, condition_bools,
            medical_conditions)

        self._create_consents(patient, consent_name, consent_signature,
                              waiver_name, waiver_signature)

        try:
            patient.sudo()._create_customer_partner()
        except Exception:
            _logger.warning('Could not link res.partner for web intake %s',
                            patient.patient_number, exc_info=True)

        return request.render('obbs_dental.patient_intake_thanks',
                              {'patient': patient, 'posted': posted})

    def _create_patient(self, posted, last_name, first_name, middle_name, sex,
                        birthdate, mobile, email, barangay, address, occupation,
                        guardian, philhealth, last_dental_visit, visit_frequency,
                        orthodontic_history, has_prosthesis, prosthesis_since,
                        referred_by, referred_reason):
        return request.env['dental.patient'].sudo().create({
            'last_name': last_name,
            'first_name': first_name,
            'middle_name': middle_name or False,
            'birthdate': birthdate,
            'sex': sex,
            'mobile': mobile,
            'email': email or False,
            'barangay': barangay,
            'home_address': address,
            'occupation': occupation or False,
            'guardian': guardian or False,
            'philhealth_number': philhealth or False,
            'source': 'web_intake',
            'intake_status': 'pending_review',
            'is_4ps_recipient': bool(posted.get('p4s_recipient')),
            'is_4ps_beneficiary': bool(posted.get('p4s_beneficiary')),
            'is_indigenous': bool(posted.get('ip')),
            'is_senior': bool(posted.get('senior')),
            'is_pwd': bool(posted.get('pwd')),
            'is_solo_parent': bool(posted.get('solo_parent')),
            'last_dental_visit': last_dental_visit,
            'dental_visit_frequency': visit_frequency or False,
            'orthodontic_history': orthodontic_history or False,
            'dental_prosthesis': has_prosthesis,
            'dental_prosthesis_since': prosthesis_since or False,
            'referred_by': referred_by or False,
            'referred_reason': referred_reason or False,
        })

    def _create_medical_history(self, patient, under_treatment,
                                under_treatment_notes, serious_illness,
                                serious_illness_notes, was_hospitalized,
                                hospitalization_notes, taking_medication,
                                medication_notes, posted, allergies, pregnant,
                                pregnancy_months, nursing, birth_control,
                                condition_bools, medical_conditions):
        vals = {
            'patient_id': patient.id,
            'date': fields.Date.today(),
            'under_medical_treatment': under_treatment,
            'smoking': bool(posted.get('tobacco')),
            'alcohol_use': bool(posted.get('alcohol_drugs')),
        }
        if under_treatment_notes:
            vals['under_medical_treatment_notes'] = under_treatment_notes
        if serious_illness_notes:
            vals['previous_surgeries'] = serious_illness_notes
        if was_hospitalized:
            vals['hospitalization'] = hospitalization_notes
            vals['hospitalization_history'] = True
        if medication_notes:
            vals['current_medication'] = medication_notes
        if allergies:
            vals['allergies'] = allergies
        if patient.sex == 'female':
            vals['pregnancy'] = pregnant
            if pregnancy_months:
                vals['pregnancy_months'] = pregnancy_months
            vals['nursing'] = nursing
            vals['birth_control_pills'] = birth_control
        vals.update(condition_bools)
        if medical_conditions:
            vals['medical_conditions'] = medical_conditions
        request.env['dental.medical.history'].sudo().create(vals)

    def _create_consents(self, patient, consent_name, consent_signature,
                         waiver_name, waiver_signature):
        consent_env = request.env['dental.consent'].sudo()
        today = fields.Date.today()
        consent_env.create({
            'patient_id': patient.id,
            'consent_type': 'data_privacy',
            'description': 'Data Privacy Consent signed via the online patient '
                           'intake form.',
            'signed_date': today,
            'signed_by': consent_name,
            'signature': consent_signature,
            'signature_name': consent_name,
            'state': 'signed',
        })
        consent_env.create({
            'patient_id': patient.id,
            'consent_type': 'waiver',
            'description': 'Extraction waiver signed via the online patient '
                           'intake form.',
            'signed_date': today,
            'signed_by': waiver_name,
            'signature': waiver_signature,
            'signature_name': waiver_name,
            'state': 'signed',
        })