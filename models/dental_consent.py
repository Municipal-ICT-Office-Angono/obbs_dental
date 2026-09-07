from odoo import models, fields, api


class DentalConsent(models.Model):
    _name = 'dental.consent'
    _description = 'Dental Consent'
    _order = 'signed_date desc, id desc'
    _rec_name = 'display_name'

    patient_id = fields.Many2one('dental.patient', string='Patient', required=True, ondelete='cascade')

    consent_type = fields.Selection([
        ('general', 'General Treatment'),
        ('data_privacy', 'Data Privacy Consent'),
        ('waiver', 'Extraction Waiver'),
        ('surgery', 'Surgery'),
        ('anesthesia', 'Anesthesia'),
        ('photo', 'Photo / Video'),
        ('xray', 'X-Ray'),
        ('implant', 'Implant'),
        ('ortho', 'Orthodontic'),
        ('other', 'Other'),
    ], string='Consent Type', required=True)

    description = fields.Text(string='Description')
    signed_date = fields.Date(string='Signed Date', default=fields.Date.today)
    expiry_date = fields.Date(string='Expiry Date')

    signed_by = fields.Char(string='Signed By')
    relationship = fields.Char(string='Relationship to Patient')

    signature = fields.Binary(string='Signature', attachment=True)
    signature_name = fields.Char(string='Signature Name')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('signed', 'Signed'),
        ('expired', 'Expired'),
    ], string='Status', default='draft')

    dentist_id = fields.Many2one('res.partner', string='Dentist', domain="[('is_company', '=', False)]")
    witness_id = fields.Many2one('res.partner', string='Witness')

    notes = fields.Text(string='Notes')

    display_name = fields.Char(string='Name', compute='_compute_display_name', store=True)

    @api.depends('consent_type', 'patient_id')
    def _compute_display_name(self):
        for rec in self:
            name = rec.patient_id.display_name or ''
            rec.display_name = f'{name} - {dict(rec._fields["consent_type"].selection).get(rec.consent_type, rec.consent_type)}'
