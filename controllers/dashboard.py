import json

from odoo import http
from odoo.http import request


class DentalDashboard(http.Controller):

    @http.route('/obbs/dashboard/data', type='http', auth='user', methods=['GET'])
    def dashboard_data(self, **params):
        report_type = (params.get('report_type') or 'monthly').strip()
        municipality = (params.get('municipality') or 'ANGONO').strip()
        province = (params.get('province') or 'Rizal').strip()

        if report_type not in ('monthly', 'quarterly', 'annual'):
            return self._json_error('Invalid report type.')
        try:
            year = int(params.get('year') or '')
        except (TypeError, ValueError):
            return self._json_error('Invalid year.')

        month = None
        quarter = None
        if report_type == 'monthly':
            try:
                month = int(params.get('month') or '')
            except (TypeError, ValueError):
                month = 0
            if not 1 <= month <= 12:
                return self._json_error('Valid month values are 1 to 12.')
        elif report_type == 'quarterly':
            try:
                quarter = int(params.get('quarter') or '')
            except (TypeError, ValueError):
                quarter = 0
            if not 1 <= quarter <= 4:
                return self._json_error('Valid quarter values are 1 to 4.')

        data = request.env['report.oral.health.generator'].get_dashboard_data(
            year, report_type, month=month, quarter=quarter,
            municipality=municipality, province=province)
        return request.make_response(
            json.dumps(data),
            headers=[('Content-Type', 'application/json; charset=utf-8')])

    @staticmethod
    def _json_error(message):
        return request.make_response(
            json.dumps({'ok': False, 'error': message}),
            headers=[('Content-Type', 'application/json; charset=utf-8')],
            status=400)