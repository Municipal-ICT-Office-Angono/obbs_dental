from odoo import models, fields, api
from odoo.exceptions import ValidationError


class DentalToothSurface(models.Model):
    _name = 'dental.tooth.surface'
    _description = 'Dental Tooth Surface'
    _rec_name = 'display_name'
    _order = 'tooth_id, surface, date desc, id desc'

    tooth_id = fields.Many2one('dental.tooth', string='Tooth', required=True, ondelete='cascade')
    patient_id = fields.Many2one(related='tooth_id.patient_id', store=True)

    surface = fields.Selection([
        ('T', 'Top (Occlusal/Incisal)'),
        ('B', 'Bottom (Cervical)'),
        ('L', 'Left (Mesial/Distal)'),
        ('R', 'Right (Distal/Mesial)'),
        ('C', 'Center (Central)'),
    ], string='Surface', required=True)

    condition = fields.Many2one('dental.condition', string='Condition', required=True)

    treatment = fields.Char(string='Treatment')
    notes = fields.Text(string='Notes')
    date = fields.Date(string='Date', default=fields.Date.today)

    display_name = fields.Char(string='Name', compute='_compute_display_name', store=True)

    @api.depends('tooth_id', 'surface')
    def _compute_display_name(self):
        surface_labels = dict(self._fields['surface'].selection)
        for rec in self:
            label = surface_labels.get(rec.surface, rec.surface)
            rec.display_name = f'{rec.tooth_id.display_name} - {label}'

    @api.model
    def create_from_chart(self, vals):
        tooth = self.env['dental.tooth'].search([
            ('patient_id', '=', vals['patient_id']),
            ('tooth_number', '=', vals['tooth_number']),
        ], limit=1)
        if not tooth:
            tooth = self.env['dental.tooth'].create({
                'patient_id': vals['patient_id'],
                'tooth_number': vals['tooth_number'],
            })

        condition = self._resolve_condition(vals.get('condition'))

        if condition.apply_to_whole_tooth:
            record = self._apply_whole_tooth(tooth, condition, vals)
        else:
            self._check_whole_tooth_conflict(tooth, condition)
            record = self._apply_surface(tooth, vals.get('surface'), condition, vals)

        tooth.patient_id.invalidate_recordset()
        return {'id': record.id, 'success': True}

    def _resolve_condition(self, condition):
        if isinstance(condition, models.Model):
            return condition
        if isinstance(condition, (int, str)):
            cond = self.env['dental.condition'].search([
                ('code', '=', condition),
            ], limit=1)
            if not cond:
                try:
                    cond = self.env['dental.condition'].browse(int(condition))
                except (ValueError, TypeError):
                    cond = self.env['dental.condition']
            if not cond.exists():
                raise ValidationError('Invalid condition.')
            return cond
        raise ValidationError('Invalid condition.')

    def _apply_whole_tooth(self, tooth, condition, vals):
        record = self.env['dental.tooth.surface']
        for srf in ['T', 'B', 'L', 'R', 'C']:
            record = self._apply_surface(tooth, srf, condition, vals)
        return record

    def _check_whole_tooth_conflict(self, tooth, condition):
        whole_tooth = tooth.surface_ids.filtered(
            lambda s: s.condition.apply_to_whole_tooth
        )
        if whole_tooth:
            raise ValidationError(
                'Tooth #%s has a whole-tooth condition (%s). '
                'Clear the whole-tooth condition before adding surface-specific conditions.'
                % (tooth.tooth_number, whole_tooth[0].condition.name)
            )

    def _apply_surface(self, tooth, surface, condition, vals):
        srf = tooth.surface_ids.filtered(lambda s: s.surface == surface)
        if srf:
            srf.write({
                'condition': condition.id,
                'treatment': vals.get('treatment') or False,
                'notes': vals.get('notes') or False,
            })
            return srf
        return self.create({
            'tooth_id': tooth.id,
            'surface': surface,
            'condition': condition.id,
            'treatment': vals.get('treatment') or False,
            'notes': vals.get('notes') or False,
        })

    def action_delete_surface(self):
        patients = self.mapped('tooth_id.patient_id')
        self.unlink()
        patients.invalidate_recordset()
