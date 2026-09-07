from odoo import models, fields, api


class DentalService(models.Model):
    _name = 'dental.service'
    _description = 'Dental Service'
    _order = 'code'
    _rec_name = 'display_name'

    code = fields.Char(string='Code', required=True)
    name = fields.Char(string='Service Name', required=True)
    display_name = fields.Char(string='Name', compute='_compute_display_name', store=True)

    _unique_code = models.Constraint('unique(code)', 'Service code must be unique.')

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f'{rec.code} - {rec.name}' if rec.code else rec.name or ''
