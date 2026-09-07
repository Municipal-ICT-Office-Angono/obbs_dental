from odoo import models, fields, api


class DentalVisit(models.Model):
    _name = 'dental.visit'
    _description = 'Dental Visit'
    _order = 'visit_date desc, id desc'
    _rec_name = 'display_name'

    patient_id = fields.Many2one('dental.patient', string='Patient', required=True, ondelete='cascade')
    visit_date = fields.Date(string='Visit Date', required=True, default=fields.Date.today)
    dentist_id = fields.Many2one('res.partner', string='Dentist', domain="[('is_company', '=', False)]")

    service_ids = fields.Many2many('dental.service', string='Services Rendered')

    referred = fields.Boolean(string='Referred')
    referral_reason = fields.Char(string='Referral Reason', placeholder='Reason(s) for referral')
    counseling = fields.Boolean(string='Counseling/Education')
    toothbrush_drill = fields.Boolean(string='Toothbrushing Drill (Under-6)')

    ofc_oral_exam = fields.Boolean(string='OFC Upon Oral Examination')
    ofc_rehabilitation = fields.Boolean(string='OFC Upon Complete Oral Rehabilitation')

    notes = fields.Text(string='Notes')
    dentist_signature = fields.Binary(string='Dentist Signature', attachment=True)

    display_name = fields.Char(string='Name', compute='_compute_display_name', store=True)

    @api.depends('patient_id', 'visit_date')
    def _compute_display_name(self):
        for rec in self:
            name = rec.patient_id.display_name or ''
            rec.display_name = f'{name} - {rec.visit_date}' if rec.visit_date else name
