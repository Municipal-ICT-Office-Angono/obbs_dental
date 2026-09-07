from odoo import models, fields, api
from odoo.exceptions import ValidationError


class OralHealthWizard(models.TransientModel):
    _name = 'report.oral.health.wizard'
    _description = 'Oral Health Form 2 Report Wizard'

    year = fields.Integer(string='Year', required=True, default=2026)
    report_type = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual'),
    ], string='Report Type', required=True, default='monthly')
    month = fields.Selection([
        ('1', 'January'), ('2', 'February'), ('3', 'March'),
        ('4', 'April'), ('5', 'May'), ('6', 'June'),
        ('7', 'July'), ('8', 'August'), ('9', 'September'),
        ('10', 'October'), ('11', 'November'), ('12', 'December'),
    ], string='Month')
    quarter = fields.Selection([
        ('1', 'Q1 (Jan-Mar)'), ('2', 'Q2 (Apr-Jun)'),
        ('3', 'Q3 (Jul-Sep)'), ('4', 'Q4 (Oct-Dec)'),
    ], string='Quarter')
    municipality = fields.Char(string='Municipality', default='ANGONO')
    province = fields.Char(string='Province', default='Rizal')

    @api.constrains('report_type', 'month')
    def _check_monthly(self):
        for rec in self:
            if rec.report_type == 'monthly' and not rec.month:
                raise ValidationError('Please select a month for monthly reports.')

    @api.constrains('report_type', 'quarter')
    def _check_quarterly(self):
        for rec in self:
            if rec.report_type == 'quarterly' and not rec.quarter:
                raise ValidationError('Please select a quarter for quarterly reports.')

    def action_generate_report(self):
        self.ensure_one()
        generator = self.env['report.oral.health.generator']
        return generator.generate_report(
            year=self.year,
            report_type=self.report_type,
            month=int(self.month) if self.month else None,
            quarter=int(self.quarter) if self.quarter else None,
            municipality=self.municipality or 'ANGONO',
            province=self.province or 'Rizal',
        )
