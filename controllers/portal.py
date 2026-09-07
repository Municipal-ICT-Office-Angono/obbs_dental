from odoo import http
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal

from .chart_geometry import build_chart


class DentalPatientPortal(CustomerPortal):

    def _get_my_patient(self):
        """Return the dental.patient linked to the current portal user's contact (sudo).

        Portal users have zero ACL on dental.* models, so all reads must be sudoed
        and strictly scoped to the caller's partner_id.
        """
        partner = request.env.user.partner_id
        return request.env['dental.patient'].sudo().search(
            [('partner_id', '=', partner.id)], limit=1)

    def _prepare_portal_layout_values(self):
        values = super()._prepare_portal_layout_values()
        values['patient'] = self._get_my_patient()
        return values

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'patient_count' in counters:
            values['patient_count'] = 1 if self._get_my_patient() else 0
        return values

    @http.route(['/my/patient'], type='http', auth='user', website=True)
    def portal_patient(self, **kw):
        """Overview page with the patient's personal details."""
        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'patient',
        })
        return request.render('obbs_dental.portal_patient_overview', values)

    @http.route(['/my/medical_history'], type='http', auth='user', website=True)
    def portal_medical_history(self, **kw):
        """Medical history for the current patient."""
        patient = self._get_my_patient()
        options = {}
        if patient:
            for opt, label in [
                ('smoking', 'Smoking'),
                ('alcohol_use', 'Alcohol Use'),
                ('pregnancy', 'Pregnancy'),
                ('bruxism', 'Bruxism'),
                ('betel_nut', 'Betel Nut Chewer'),
                ('tattoo', 'Tattoo'),
                ('hypertension', 'Hypertension/CVA'),
                ('diabetes', 'Diabetes Mellitus'),
                ('blood_disorders', 'Blood Disorders'),
                ('cardiovascular', 'Cardiovascular/Heart Disease'),
                ('thyroid_disorders', 'Thyroid Disorders'),
                ('hepatitis', 'Hepatitis'),
                ('malignancy', 'Malignancy'),
                ('hospitalization_history', 'History of Hospitalization'),
                ('blood_transfusion', 'Blood Transfusion'),
            ]:
                options[opt] = label
        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'medical_history',
            'records': patient.medical_history_ids.sudo() if patient else [],
            'options': options,
        })
        return request.render('obbs_dental.portal_medical_history', values)

    @http.route(['/my/dental_history'], type='http', auth='user', website=True)
    def portal_dental_history(self, **kw):
        """Dental history entries and visits for the current patient."""
        patient = self._get_my_patient()
        conditions = request.env['dental.condition'].sudo().search([])
        cond_labels = {c.code: c.name for c in conditions}
        cond_colors = {c.code: c.color for c in conditions}
        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'dental_history',
            'entries': sorted(patient.dental_history_ids.sudo(), key=lambda r: r.date, reverse=True) if patient else [],
            'visits': sorted(request.env['dental.visit'].sudo().search([('patient_id', '=', patient.id)]), key=lambda r: r.visit_date, reverse=True) if patient else [],
            'cond_labels': cond_labels,
            'cond_colors': cond_colors,
        })
        return request.render('obbs_dental.portal_dental_history', values)

    @http.route(['/my/dental_chart'], type='http', auth='user', website=True)
    def portal_dental_chart(self, **kw):
        """Read-only dental chart (odontogram) for the current patient."""
        patient = self._get_my_patient()
        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'dental_chart',
            'chart': build_chart(patient) if patient else None,
        })
        return request.render('obbs_dental.portal_dental_chart', values)