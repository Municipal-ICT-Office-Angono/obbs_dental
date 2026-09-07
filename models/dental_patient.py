from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re


class DentalPatient(models.Model):
    _name = 'dental.patient'
    _description = 'Dental Patient'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'
    _order = 'patient_number desc'

    patient_number = fields.Char(
        string='Patient Number',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self._default_patient_number(),
    )

    partner_id = fields.Many2one('res.partner', string='Contact', ondelete='restrict')

    portal_user_ids = fields.Many2many(
        'res.users',
        compute='_compute_portal_user_ids',
        string='Portal Users',
        readonly=True,
    )

    last_name = fields.Char(string='Last Name', required=True, tracking=True)
    first_name = fields.Char(string='First Name', required=True, tracking=True)
    middle_name = fields.Char(string='Middle Name')

    display_name = fields.Char(string='Name', compute='_compute_display_name', store=True)

    birthdate = fields.Date(string='Birthdate', tracking=True)
    age = fields.Integer(string='Age', compute='_compute_age', store=True)

    sex = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ], string='Sex', required=True, tracking=True)

    blood_type = fields.Selection([
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ], string='Blood Type')

    nationality = fields.Char(string='Nationality')
    religion = fields.Char(string='Religion')
    occupation = fields.Char(string='Occupation')

    home_address = fields.Text(string='Home Address')
    mobile = fields.Char(string='Mobile Number')
    email = fields.Char(string='Email Address')

    dental_insurance = fields.Char(string='Dental Insurance')
    guardian = fields.Char(string='Guardian')
    emergency_contact = fields.Char(string='Emergency Contact')

    source = fields.Selection([
        ('walk_in', 'Walk-in'),
        ('web_intake', 'Web Intake'),
    ], string='Source', default='walk_in')
    intake_status = fields.Selection([
        ('pending_review', 'Pending Review'),
        ('processed', 'Processed'),
    ], string='Intake Status')

    barangay = fields.Char(string='Barangay')
    philhealth_number = fields.Char(string='PhilHealth Number')

    is_4ps_recipient = fields.Boolean(string='4Ps Recipient')
    is_4ps_beneficiary = fields.Boolean(string='4Ps Beneficiary')
    is_indigenous = fields.Boolean(string='Indigenous People (IP)')
    is_senior = fields.Boolean(string='Senior Citizen')
    is_pwd = fields.Boolean(string='Person with Disability (PWD)')
    is_solo_parent = fields.Boolean(string='Solo Parent')

    last_dental_visit = fields.Date(string='Last Dental Visit')
    dental_visit_frequency = fields.Selection([
        ('twice_year', 'At least twice a year'),
        ('once_year', 'Once a year'),
        ('never', 'Never'),
    ], string='Dental Visit Frequency')
    orthodontic_history = fields.Char(string='Orthodontic Treatment History')
    dental_prosthesis = fields.Boolean(string='Has Dental Prosthesis')
    dental_prosthesis_since = fields.Char(string='Dental Prosthesis Since')
    referred_by = fields.Char(string='Referred By')
    referred_reason = fields.Char(string='Referral Reason')

    signature = fields.Binary(string='Signature', attachment=True)
    signature_name = fields.Char(string='Signature Name')

    medical_history_ids = fields.One2many('dental.medical.history', 'patient_id', string='Medical History')
    dental_history_ids = fields.One2many('dental.history', 'patient_id', string='Dental History')
    tooth_ids = fields.One2many('dental.tooth', 'patient_id', string='Teeth')
    tooth_surface_ids = fields.One2many(
        'dental.tooth.surface',
        compute='_compute_tooth_surface_ids',
        string='Tooth Surfaces',
        readonly=True,
    )
    consent_ids = fields.One2many('dental.consent', 'patient_id', string='Consents')
    clinical_finding_ids = fields.One2many(
        'dental.clinical.finding',
        'patient_id',
        string='Clinical Findings',
    )

    active = fields.Boolean(string='Active', default=True)

    tooth_conditions = fields.Text(
        string='Tooth Conditions',
        compute='_compute_tooth_conditions',
        store=False,
    )

    _unique_patient_number = models.Constraint(
        'unique (patient_number)',
        'Patient Number must be unique.',
    )

    @api.model
    def _default_patient_number(self):
        seq = self.env['ir.sequence'].next_by_code('dental.patient') or '/'
        return seq

    @api.depends('last_name', 'first_name', 'middle_name')
    def _compute_display_name(self):
        for rec in self:
            parts = [rec.first_name, rec.middle_name, rec.last_name]
            rec.display_name = ' '.join(p for p in parts if p)

    @api.depends('partner_id')
    def _compute_portal_user_ids(self):
        users = self.env['res.users'].sudo()
        for rec in self:
            if rec.partner_id:
                rec.portal_user_ids = users.search([('partner_id', '=', rec.partner_id.id)])
            else:
                rec.portal_user_ids = False

    def _partner_vals(self):
        self.ensure_one()
        vals = {
            'name': self.display_name or (self.first_name or self.last_name),
            'type': 'contact',
            'is_company': False,
        }
        if self.email:
            vals['email'] = self.email
        if self.mobile:
            vals['phone'] = self.mobile
        if self.home_address:
            lines = [ln.strip() for ln in self.home_address.split('\n') if ln.strip()]
            if lines:
                vals['street'] = lines[0]
                if len(lines) > 1:
                    vals['street2'] = '\n'.join(lines[1:])
        return vals

    def _create_customer_partner(self):
        self.ensure_one()
        partner = self.partner_id
        if not partner and self.email:
            other = self.env['dental.patient'].search([
                ('id', '!=', self.id),
                ('email', '=ilike', self.email),
            ], limit=1)
            if other and other.partner_id:
                partner = other.partner_id
            else:
                partner = self.env['res.partner'].search([
                    ('email', '=ilike', self.email),
                    ('type', '=', 'contact'),
                ], limit=1)
                if partner and self.env['dental.patient'].search_count([
                    ('partner_id', '=', partner.id),
                    ('id', '!=', self.id),
                ]):
                    partner = self.env['res.partner']
        if not partner:
            partner = self.env['res.partner'].create(self._partner_vals())
        else:
            self._sync_partner()
        if self.partner_id.id != partner.id:
            self.write({'partner_id': partner.id})
        return partner

    def _sync_partner(self):
        self.ensure_one()
        if not self.partner_id:
            return
        vals = self._partner_vals()
        if vals:
            self.partner_id.write(vals)

    def write(self, vals):
        res = super().write(vals)
        if res and vals.keys() & {
                'last_name', 'first_name', 'middle_name',
                'email', 'mobile', 'home_address'}:
            for rec in self:
                rec._sync_partner()
        return res

    def action_create_portal_user(self):
        self.ensure_one()
        if not self.email:
            raise ValidationError(
                'Cannot create portal login: the patient has no e-mail address.'
            )
        partner = self._create_customer_partner()

        users_env = self.env['res.users'].sudo()
        user = users_env.search([('login', '=ilike', self.email)], limit=1)
        if not user:
            user = users_env.create({
                'name': self.display_name,
                'login': self.email,
                'partner_id': partner.id,
                'group_ids': [(6, 0, [self.env.ref('base.group_portal').id])],
            })
        else:
            same_partner = user.partner_id.id == partner.id
            is_internal = self.env.ref('base.group_user').id in user.all_group_ids.ids
            if not same_partner and is_internal:
                raise ValidationError(
                    'The e-mail %s is already used by an internal user. '
                    'Use a different e-mail address for portal access.' % self.email
                )
            vals = {'group_ids': [(4, self.env.ref('base.group_portal').id)]}
            if not same_partner:
                vals['partner_id'] = partner.id
            if user.name != self.display_name:
                vals['name'] = self.display_name
            user.write(vals)

        partner.signup_prepare('signup')
        template = self.env.ref('auth_signup.portal_set_password_email')
        template.with_context(force_send=True).send_mail(user.id)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Invitation Sent',
                'message': 'An invitation e-mail was sent to %s to create '
                           'their portal login.' % self.email,
                'type': 'success',
                'sticky': False,
            },
        }

    def action_mark_intake_processed(self):
        self.ensure_one()
        self.write({'intake_status': 'processed'})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Intake Processed',
                'message': 'Patient %s has been marked as processed.' % self.display_name,
                'type': 'success',
                'sticky': False,
            },
        }

    def action_reset_intake_pending(self):
        self.ensure_one()
        self.write({'intake_status': 'pending_review'})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Intake Reopened',
                'message': 'Patient %s is back in the pending review queue.' % self.display_name,
                'type': 'info',
                'sticky': False,
            },
        }

    def action_new_clinical_finding(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'New Clinical Finding',
            'res_model': 'dental.clinical.finding',
            'view_mode': 'form',
            'target': 'current',
            'context': {'default_patient_id': self.id},
        }

    @api.depends('birthdate')
    def _compute_age(self):
        from datetime import date
        for rec in self:
            if rec.birthdate:
                today = date.today()
                age = today.year - rec.birthdate.year - (
                    (today.month, today.day) < (rec.birthdate.month, rec.birthdate.day)
                )
                rec.age = age
            else:
                rec.age = 0

    @api.constrains('mobile')
    def _check_mobile(self):
        for rec in self:
            if rec.mobile and not re.match(r'^\+?[\d\s\-()]{7,20}$', rec.mobile):
                raise ValidationError('Invalid mobile number format.')

    @api.constrains('email')
    def _check_email(self):
        for rec in self:
            if rec.email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', rec.email):
                raise ValidationError('Invalid email address format.')

    @api.depends('tooth_ids', 'tooth_ids.surface_ids', 'tooth_ids.surface_ids.condition',
                 'tooth_ids.surface_ids.condition.code', 'tooth_ids.surface_ids.condition.name',
                 'tooth_ids.surface_ids.condition.color', 'tooth_ids.surface_ids.condition.apply_to_whole_tooth',
                 'tooth_ids.surface_ids.treatment', 'tooth_ids.surface_ids.notes')
    def _compute_tooth_conditions(self):
        import json
        for rec in self:
            data = {}
            for tooth in rec.tooth_ids:
                tn = tooth.tooth_number
                latest = {}
                for srf in tooth.surface_ids.sorted('date', reverse=True):
                    if srf.surface not in latest:
                        latest[srf.surface] = {
                            'condition': srf.condition.code if srf.condition else None,
                            'label': srf.condition.name if srf.condition else None,
                            'color': srf.condition.color if srf.condition else None,
                            'wholeTooth': srf.condition.apply_to_whole_tooth if srf.condition else False,
                            'treatment': srf.treatment,
                            'notes': srf.notes,
                            'date': str(srf.date) if srf.date else None,
                        }
                if latest:
                    data[tn] = {'surfaces': latest}
            rec.tooth_conditions = json.dumps(data)

    @api.depends('tooth_ids', 'tooth_ids.surface_ids')
    def _compute_tooth_surface_ids(self):
        for rec in self:
            rec.tooth_surface_ids = rec.mapped('tooth_ids.surface_ids')
