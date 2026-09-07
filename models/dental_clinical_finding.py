from odoo import models, fields, api


class DentalClinicalFinding(models.Model):
    _name = 'dental.clinical.finding'
    _description = 'Dental Clinical Finding'
    _order = 'date desc, id desc'
    _rec_name = 'display_name'
    _inherit = ['mail.thread']

    patient_id = fields.Many2one('dental.patient', string='Patient', required=True, ondelete='cascade')
    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    dentist_id = fields.Many2one('res.partner', string='Dentist', domain="[('is_company', '=', False)]")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Completed'),
    ], string='Status', default='draft', tracking=True)

    periodontal_disease = fields.Boolean(string='Periodontal Disease', tracking=True)
    periodontal_teeth = fields.Char(string='Affected Teeth', placeholder='e.g. 16, 26, 31')
    mobility = fields.Selection([
        ('I', 'Grade I'),
        ('II', 'Grade II'),
        ('III', 'Grade III'),
    ], string='Grade of Mobility')

    torus_palatinus = fields.Boolean(string='Torus Palatinus')
    torus_mandibularis = fields.Boolean(string='Torus Mandibularis')
    epulis_cyst_tumor = fields.Boolean(string='Epulis Fisuratum / Cyst / Tumor')

    prosthesis_cd_upper = fields.Boolean(string='Complete Denture (Upper)')
    prosthesis_cd_lower = fields.Boolean(string='Complete Denture (Lower)')
    prosthesis_rpd_upper = fields.Boolean(string='RPD (Upper)')
    prosthesis_rpd_lower = fields.Boolean(string='RPD (Lower)')
    prosthesis_fpd_upper = fields.Boolean(string='FPD (Upper)')
    prosthesis_fpd_lower = fields.Boolean(string='FPD (Lower)')
    prosthesis_years = fields.Char(string='Prosthesis Years in Use')

    ridge_height_upper = fields.Selection([
        ('normal', 'Normal'),
        ('low', 'Low'),
    ], string='Ridge Height (Upper)')
    ridge_height_lower = fields.Selection([
        ('normal', 'Normal'),
        ('low', 'Low'),
    ], string='Ridge Height (Lower)')

    rx_root_planing_scaling = fields.Boolean(string='Root Planing & Scaling')
    rx_extraction = fields.Boolean(string='Extraction of Affected Tooth/Teeth')
    rx_surgical_torus = fields.Boolean(string='Surgical Removal (Torus)')
    rx_surgical_biopsy = fields.Boolean(string='Surgical Removal / Biopsy')
    rx_prosthesis_repair = fields.Boolean(string='Prosthesis For Repair')
    rx_prosthesis_replacement = fields.Boolean(string='Prosthesis For Replacement / New')

    teeth_with_caries = fields.Integer(string='No. of Teeth with Dental Caries')
    oral_debris_calculus = fields.Boolean(string='Presence of Oral Debris / Calculus')
    gingivitis_periodontitis = fields.Boolean(string='Presence of Gingivitis / Periodontitis')
    dento_facial_anomaly = fields.Boolean(string='Presence of Dento-facial Anomaly')
    soft_tissue_lesions = fields.Boolean(string='Presence of Soft Tissue Lesions')
    permanent_teeth_present = fields.Integer(string='No. of Permanent Teeth Present')
    deciduous_teeth_present = fields.Integer(string='No. of Deciduous Teeth Present')
    oro_facial_anomaly = fields.Boolean(string='Presence of Oro-facial Anomaly')
    oro_facial_anomaly_type = fields.Char(string='Type of Oro-facial Anomaly')
    oral_lesions = fields.Boolean(string='Presence of Oral Lesions')
    oral_lesions_type = fields.Char(string='Type of Oral Lesions')

    assessed_by = fields.Many2one('res.partner', string='Assessed By', domain="[('is_company', '=', False)]")
    assessed_position = fields.Char(string='Position')

    clinical_notes = fields.Text(string='Clinical Notes')
    attachment_ids = fields.Many2many('ir.attachment', string='X-Ray / Photos')

    display_name = fields.Char(string='Name', compute='_compute_display_name', store=True)

    @api.depends('patient_id', 'date')
    def _compute_display_name(self):
        for rec in self:
            name = rec.patient_id.display_name or ''
            rec.display_name = f'{name} - {rec.date}' if rec.date else name

    def action_confirm(self):
        patients = self.mapped('patient_id').filtered(
            lambda p: p.source == 'web_intake' and p.intake_status == 'pending_review'
        )
        if patients:
            patients.write({'intake_status': 'processed'})
        self.write({'state': 'done'})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Assessment Completed',
                'message': 'Clinical finding confirmed. The patient intake was '
                           'marked as processed when applicable.',
                'type': 'success',
                'sticky': False,
            },
        }

    def action_back_draft(self):
        self.write({'state': 'draft'})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Assessment Reopened',
                'message': 'Clinical finding is back in draft state.',
                'type': 'info',
                'sticky': False,
            },
        }