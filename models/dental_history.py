from odoo import models, fields, api


class DentalHistory(models.Model):
    _name = 'dental.history'
    _description = 'Dental History (Odontogram)'
    _order = 'date desc, id desc'
    _rec_name = 'display_name'

    patient_id = fields.Many2one('dental.patient', string='Patient', required=True, ondelete='cascade')

    tooth_number = fields.Char(string='Tooth Number', required=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.today)

    condition = fields.Selection([
        ('PR', 'Present Tooth'),
        ('D', 'Decayed (Caries)'),
        ('Am', 'Amalgam Filling'),
        ('Co', 'Composite Filling'),
        ('JC', 'Jacket Crown'),
        ('In', 'Inlay'),
        ('S', 'Sealant'),
        ('M', 'Missing due to Caries'),
        ('MO', 'Missing due to Other Cause'),
        ('X', 'Extraction due to Caries'),
        ('XO', 'Extraction due to Other Cause'),
        ('Rf', 'Root Fragment'),
        ('Im', 'Impacted Tooth'),
        ('Un', 'Unerupted'),
        ('Sp', 'Supernumerary Tooth'),
        ('BR', 'Bruxism'),
        ('ABR', 'Abrasion'),
        ('ABF', 'Abfraction'),
        ('Imp', 'Implant'),
        ('Abu', 'Abutment'),
        ('Att', 'Attachment'),
        ('Po', 'Pontic'),
        ('Rm', 'Removable Denture'),
        ('Gi', 'Gingivitis'),
        ('PD', 'Periodontal Disease'),
        ('OD', 'Oral Debris'),
        ('Ca', 'Calculus'),
        ('DFA', 'Dento-Facial Anomaly'),
    ], string='Condition', required=True)

    surface = fields.Selection([
        ('T', 'Top'),
        ('B', 'Bottom'),
        ('L', 'Left'),
        ('R', 'Right'),
        ('C', 'Center'),
    ], string='Surface')

    arch = fields.Selection([
        ('upper', 'Upper'),
        ('lower', 'Lower'),
    ], string='Arch', compute='_compute_arch', store=True)

    quadrant = fields.Selection([
        ('UR', 'Upper Right'),
        ('UL', 'Upper Left'),
        ('LR', 'Lower Right'),
        ('LL', 'Lower Left'),
    ], string='Quadrant', compute='_compute_quadrant', store=True)

    treatment = fields.Char(string='Treatment')
    notes = fields.Text(string='Notes')
    dentist_id = fields.Many2one('res.partner', string='Dentist', domain="[('is_company', '=', False)]")

    display_name = fields.Char(string='Name', compute='_compute_display_name', store=True)

    @api.depends('tooth_number', 'patient_id')
    def _compute_display_name(self):
        for rec in self:
            name = rec.patient_id.display_name or ''
            rec.display_name = f'{name} - Tooth #{rec.tooth_number}'

    @api.depends('tooth_number')
    def _compute_arch(self):
        for rec in self:
            num = rec._parse_tooth_number()
            if num >= 11 and num <= 28:
                rec.arch = 'upper'
            elif num >= 31 and num <= 48:
                rec.arch = 'lower'
            elif num >= 51 and num <= 85:
                rec.arch = 'upper' if num >= 51 and num <= 65 else 'lower'
            else:
                rec.arch = False

    @api.depends('tooth_number')
    def _compute_quadrant(self):
        for rec in self:
            num = rec._parse_tooth_number()
            if num >= 11 and num <= 18:
                rec.quadrant = 'UR'
            elif num >= 21 and num <= 28:
                rec.quadrant = 'UL'
            elif num >= 31 and num <= 38:
                rec.quadrant = 'LL'
            elif num >= 41 and num <= 48:
                rec.quadrant = 'LR'
            elif num >= 51 and num <= 55:
                rec.quadrant = 'UR'
            elif num >= 61 and num <= 65:
                rec.quadrant = 'UL'
            elif num >= 71 and num <= 75:
                rec.quadrant = 'LL'
            elif num >= 81 and num <= 85:
                rec.quadrant = 'LR'
            else:
                rec.quadrant = False

    def _parse_tooth_number(self):
        try:
            return int(self.tooth_number)
        except (ValueError, TypeError):
            return 0

    @api.model
    def create_from_chart(self, vals):
        record = self.create({
            'patient_id': vals.get('patient_id'),
            'tooth_number': vals.get('tooth_number'),
            'condition': vals.get('condition'),
            'treatment': vals.get('treatment'),
            'notes': vals.get('notes'),
            'date': fields.Date.today(),
        })
        return {'id': record.id, 'success': True}

    @api.model
    def _log_surface(self, tooth, surface, condition, vals):
        """Append the chart change to the dated treatment log.

        ``dental.tooth.surface`` only holds the *current* state of each sector,
        so nothing would ever show up in the Dental History tab or on the
        patient portal without this. Re-saving an identical state is ignored.
        """
        if not tooth or not condition or not tooth.patient_id:
            return self.browse()
        patient = tooth.patient_id
        treatment = vals.get('treatment') or False
        notes = vals.get('notes') or False
        last = self.search([
            ('patient_id', '=', patient.id),
            ('tooth_number', '=', tooth.tooth_number),
            ('surface', '=', surface or False),
        ], limit=1, order='id desc')
        if (last and last.condition == condition.code
                and (last.treatment or False) == treatment
                and (last.notes or False) == notes):
            return last
        return self.create({
            'patient_id': patient.id,
            'tooth_number': tooth.tooth_number,
            'surface': surface or False,
            'condition': condition.code,
            'treatment': treatment,
            'notes': notes,
            'date': fields.Date.today(),
        })
