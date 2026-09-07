from odoo import models, fields, api


class DentalMedicalHistory(models.Model):
    _name = 'dental.medical.history'
    _description = 'Dental Medical History'
    _order = 'date desc, id desc'
    _rec_name = 'display_name'

    patient_id = fields.Many2one('dental.patient', string='Patient', required=True, ondelete='cascade')

    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    version = fields.Integer(string='Version', compute='_compute_version', store=True)

    general_health = fields.Text(string='General Health')
    current_medication = fields.Text(string='Current Medication')
    previous_surgeries = fields.Text(string='Previous Surgeries')
    hospitalization = fields.Text(string='Hospitalization')

    smoking = fields.Boolean(string='Smoking')
    alcohol_use = fields.Boolean(string='Alcohol Use')
    pregnancy = fields.Boolean(string='Pregnancy')
    bruxism = fields.Boolean(string='Bruxism')
    betel_nut = fields.Boolean(string='Betel Nut Chewer')
    tattoo = fields.Boolean(string='Tattoo')

    allergies = fields.Text(string='Allergies')
    medical_conditions = fields.Text(string='Medical Conditions')

    under_medical_treatment = fields.Boolean(string='Under Medical Treatment')
    under_medical_treatment_notes = fields.Text(string='Medical Treatment Details')
    nursing = fields.Boolean(string='Nursing')
    birth_control_pills = fields.Boolean(string='Birth Control Pills')
    pregnancy_months = fields.Char(string='Pregnancy (months)')

    hypertension = fields.Boolean(string='Hypertension/CVA')
    diabetes = fields.Boolean(string='Diabetes Mellitus')
    blood_disorders = fields.Boolean(string='Blood Disorders')
    cardiovascular = fields.Boolean(string='Cardiovascular/Heart Disease')
    thyroid_disorders = fields.Boolean(string='Thyroid Disorders')
    hepatitis = fields.Boolean(string='Hepatitis')
    malignancy = fields.Boolean(string='Malignancy')
    hospitalization_history = fields.Boolean(string='History of Hospitalization')
    blood_transfusion = fields.Boolean(string='Blood Transfusion')

    notes = fields.Text(string='Notes')
    created_by = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)

    display_name = fields.Char(string='Name', compute='_compute_display_name', store=True)

    @api.depends('date', 'patient_id')
    def _compute_display_name(self):
        for rec in self:
            name = rec.patient_id.display_name or ''
            rec.display_name = f'{name} - {rec.date}' if rec.date else name

    @api.depends('date', 'patient_id')
    def _compute_version(self):
        for rec in self:
            existing = self.search([
                ('patient_id', '=', rec.patient_id.id),
                ('date', '<=', rec.date or fields.Date.today()),
                ('id', '!=', rec.id),
            ], order='date desc, id desc', limit=1)
            rec.version = (existing.version or 0) + 1
