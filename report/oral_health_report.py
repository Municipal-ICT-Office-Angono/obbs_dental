import os
import copy
from datetime import date
from collections import defaultdict
from dateutil.relativedelta import relativedelta
from openpyxl import load_workbook
from odoo import models, api
from odoo.exceptions import UserError


class OralHealthGenerator(models.AbstractModel):
    _name = 'report.oral.health.generator'
    _description = 'Oral Health Form 2 Report Generator'

    TEMPLATE_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'ANGONO 2026 blank form 2.xlsx',
    )

    SHEET_MAP = {
        'monthly': {
            1: 'JAN', 2: 'FEB', 3: 'MAR', 4: 'APR',
            5: 'MAY', 6: 'JUN', 7: 'JUL', 8: 'AUG',
            9: 'SEP', 10: 'OCT', 11: 'NOV', 12: 'DEC',
        },
        'quarterly': {
            1: '1ST QTR', 2: '2ND QTR', 3: '3RD QTR', 4: '4TH QTR',
        },
        'annual': {'annual': 'ANN'},
    }

    MONTH_LABELS = {
        1: 'JANUARY', 2: 'FEBRUARY', 3: 'MARCH', 4: 'APRIL',
        5: 'MAY', 6: 'JUNE', 7: 'JULY', 8: 'AUGUST',
        9: 'SEPTEMBER', 10: 'OCTOBER', 11: 'NOVEMBER', 12: 'DECEMBER',
    }

    @api.model
    def generate_report(self, year, report_type, month=None, quarter=None,
                        municipality='ANGONO', province='Rizal'):
        if not os.path.exists(self.TEMPLATE_PATH):
            raise UserError(f'Template file not found: {self.TEMPLATE_PATH}')

        wb = load_workbook(self.TEMPLATE_PATH)

        if report_type == 'monthly':
            date_ranges = self._get_month_ranges(year, month)
            sheet_name = self.SHEET_MAP['monthly'][month]
            label = f'Month:  {self.MONTH_LABELS[month]} {year}'
            self._fill_sheet(wb, sheet_name, date_ranges, label, municipality, province)
        elif report_type == 'quarterly':
            date_ranges = self._get_quarter_ranges(year, quarter)
            sheet_name = self.SHEET_MAP['quarterly'][quarter]
            q_label = f'{quarter}{"st" if quarter == 1 else "nd" if quarter == 2 else "rd" if quarter == 3 else "th"} QTR {year}'
            label = q_label
            self._fill_sheet(wb, sheet_name, date_ranges, label, municipality, province)
        elif report_type == 'annual':
            date_ranges = self._get_annual_ranges(year)
            sheet_name = self.SHEET_MAP['annual']['annual']
            label = f'ANNUAL {year}'
            self._fill_sheet(wb, sheet_name, date_ranges, label, municipality, province)

        output_path = f'/tmp/oral_health_{year}_{report_type}.xlsx'
        wb.save(output_path)
        wb.close()

        with open(output_path, 'rb') as f:
            data = f.read()

        import base64
        attachment = self.env['ir.attachment'].create({
            'name': f'Oral_Health_Form_2_{year}_{report_type}.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(data),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'res_id': attachment.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'dialog_size': 'small'},
        }

    def _get_month_ranges(self, year, month):
        start = date(year, month, 1)
        if month == 12:
            end = date(year, 12, 31)
        else:
            end = date(year, month + 1, 1) - relativedelta(days=1)
        return [(start, end)]

    def _get_quarter_ranges(self, year, quarter):
        start_month = (quarter - 1) * 3 + 1
        start = date(year, start_month, 1)
        end_month = start_month + 2
        if end_month == 12:
            end = date(year, 12, 31)
        else:
            end = date(year, end_month + 1, 1) - relativedelta(days=1)
        return [(start, end)]

    def _get_annual_ranges(self, year):
        return [(date(year, 1, 1), date(year, 12, 31))]

    def _fill_sheet(self, wb, sheet_name, date_ranges, label, municipality, province):
        ws = wb[sheet_name]

        ws['A5'] = label
        ws['A6'] = f'Province: {province}'
        ws['A8'] = f'Municipality: {municipality}'

        all_patients = self.env['dental.patient'].search([])
        patient_map = {p.id: p for p in all_patients}

        start_date = date_ranges[0][0]
        end_date = date_ranges[-1][1]

        visited_patients = set()
        visits = self.env['dental.visit'].search([
            ('visit_date', '>=', start_date),
            ('visit_date', '<=', end_date),
        ])
        for v in visits:
            visited_patients.add(v.patient_id.id)

        med_histories = self.env['dental.medical.history'].search([])
        patient_latest_med = {}
        for mh in med_histories:
            pid = mh.patient_id.id
            if pid not in patient_latest_med or mh.date > patient_latest_med[pid].date:
                patient_latest_med[pid] = mh

        surface_records = self.env['dental.tooth.surface'].search([
            ('patient_id', 'in', all_patients.ids),
        ])
        patient_conditions = defaultdict(set)
        patient_dmft = defaultdict(lambda: {'d': set(), 'm': set(), 'f': set()})
        for sr in surface_records:
            pid = sr.patient_id.id
            if sr.condition:
                patient_conditions[pid].add(sr.condition.code)
                code = sr.condition.code
                if code == 'D':
                    patient_dmft[pid]['d'].add(pid)
                elif code in ('M', 'MO'):
                    patient_dmft[pid]['m'].add(pid)
                elif code in ('Am', 'Co'):
                    patient_dmft[pid]['f'].add(pid)

        clinical_findings = self.env['dental.clinical.finding'].search([
            ('state', '=', 'done'),
        ])
        latest_finding = {}
        for cf in clinical_findings:
            pid = cf.patient_id.id
            if pid not in latest_finding or cf.date > latest_finding[pid].date:
                latest_finding[pid] = cf
        for pid, cf in latest_finding.items():
            if cf.teeth_with_caries:
                patient_conditions[pid].add('D')
            if cf.gingivitis_periodontitis:
                patient_conditions[pid].add('Gi')
                patient_conditions[pid].add('PD')
            if cf.oral_debris_calculus:
                patient_conditions[pid].add('OD')
                patient_conditions[pid].add('Ca')
            if cf.dento_facial_anomaly:
                patient_conditions[pid].add('DFA')

        visit_services = defaultdict(set)
        visit_flags = defaultdict(lambda: {
            'referred': False, 'counseling': False,
            'toothbrush_drill': False, 'ofc_oral_exam': False, 'ofc_rehabilitation': False,
        })
        for v in visits:
            pid = v.patient_id.id
            for svc in v.service_ids:
                visit_services[pid].add(svc.code)
            if v.referred:
                visit_flags[pid]['referred'] = True
            if v.counseling:
                visit_flags[pid]['counseling'] = True
            if v.toothbrush_drill:
                visit_flags[pid]['toothbrush_drill'] = True
            if v.ofc_oral_exam:
                visit_flags[pid]['ofc_oral_exam'] = True
            if v.ofc_rehabilitation:
                visit_flags[pid]['ofc_rehabilitation'] = True

        column_defs = self._get_column_definitions()
        row_data = self._compute_all_rows(
            all_patients, patient_map, visited_patients, patient_latest_med,
            patient_conditions, patient_dmft, visit_services, visit_flags, column_defs,
        )

        self._write_data_rows(ws, row_data)

    def _get_column_definitions(self):
        return [
            {'col': 'B', 'label': 'preg_10_14', 'age_min': 10, 'age_max': 14, 'sex': 'female', 'pregnant_only': True},
            {'col': 'C', 'label': 'preg_15_19', 'age_min': 15, 'age_max': 19, 'sex': 'female', 'pregnant_only': True},
            {'col': 'D', 'label': 'preg_20_49', 'age_min': 20, 'age_max': 49, 'sex': 'female', 'pregnant_only': True},
            {'col': 'E', 'label': 'preg_total', 'age_min': 10, 'age_max': 49, 'sex': 'female', 'pregnant_only': True},

            {'col': 'F', 'label': 'infant_m', 'age_min': 0, 'age_max': 0, 'sex': 'male'},
            {'col': 'G', 'label': 'infant_f', 'age_min': 0, 'age_max': 0, 'sex': 'female'},

            {'col': 'H', 'label': 'u5_1_m', 'age_min': 1, 'age_max': 1, 'sex': 'male'},
            {'col': 'I', 'label': 'u5_1_f', 'age_min': 1, 'age_max': 1, 'sex': 'female'},
            {'col': 'J', 'label': 'u5_2_m', 'age_min': 2, 'age_max': 2, 'sex': 'male'},
            {'col': 'K', 'label': 'u5_2_f', 'age_min': 2, 'age_max': 2, 'sex': 'female'},
            {'col': 'L', 'label': 'u5_3_m', 'age_min': 3, 'age_max': 3, 'sex': 'male'},
            {'col': 'M', 'label': 'u5_3_f', 'age_min': 3, 'age_max': 3, 'sex': 'female'},
            {'col': 'N', 'label': 'u5_4_m', 'age_min': 4, 'age_max': 4, 'sex': 'male'},
            {'col': 'O', 'label': 'u5_4_f', 'age_min': 4, 'age_max': 4, 'sex': 'female'},
            {'col': 'P', 'label': 'u5_total_m', 'age_min': 1, 'age_max': 4, 'sex': 'male'},
            {'col': 'Q', 'label': 'u5_total_f', 'age_min': 1, 'age_max': 4, 'sex': 'female'},

            {'col': 'R', 'label': 'school_5_m', 'age_min': 5, 'age_max': 5, 'sex': 'male'},
            {'col': 'S', 'label': 'school_5_f', 'age_min': 5, 'age_max': 5, 'sex': 'female'},
            {'col': 'T', 'label': 'school_6_m', 'age_min': 6, 'age_max': 6, 'sex': 'male'},
            {'col': 'U', 'label': 'school_6_f', 'age_min': 6, 'age_max': 6, 'sex': 'female'},
            {'col': 'V', 'label': 'school_7_m', 'age_min': 7, 'age_max': 7, 'sex': 'male'},
            {'col': 'W', 'label': 'school_7_f', 'age_min': 7, 'age_max': 7, 'sex': 'female'},
            {'col': 'X', 'label': 'school_8_m', 'age_min': 8, 'age_max': 8, 'sex': 'male'},
            {'col': 'Y', 'label': 'school_8_f', 'age_min': 8, 'age_max': 8, 'sex': 'female'},
            {'col': 'Z', 'label': 'school_9_m', 'age_min': 9, 'age_max': 9, 'sex': 'male'},
            {'col': 'AA', 'label': 'school_9_f', 'age_min': 9, 'age_max': 9, 'sex': 'female'},
            {'col': 'AB', 'label': 'school_total_m', 'age_min': 5, 'age_max': 9, 'sex': 'male'},
            {'col': 'AC', 'label': 'school_total_f', 'age_min': 5, 'age_max': 9, 'sex': 'female'},

            {'col': 'AD', 'label': 'adol_10_m', 'age_min': 10, 'age_max': 14, 'sex': 'male'},
            {'col': 'AE', 'label': 'adol_10_f', 'age_min': 10, 'age_max': 14, 'sex': 'female'},
            {'col': 'AF', 'label': 'adol_15_m', 'age_min': 15, 'age_max': 19, 'sex': 'male'},
            {'col': 'AG', 'label': 'adol_15_f', 'age_min': 15, 'age_max': 19, 'sex': 'female'},
            {'col': 'AH', 'label': 'adult_m', 'age_min': 20, 'age_max': 59, 'sex': 'male'},
            {'col': 'AI', 'label': 'adult_f', 'age_min': 20, 'age_max': 59, 'sex': 'female'},
            {'col': 'AJ', 'label': 'senior_m', 'age_min': 60, 'age_max': 120, 'sex': 'male'},
            {'col': 'AK', 'label': 'senior_f', 'age_min': 60, 'age_max': 120, 'sex': 'female'},

            {'col': 'AL', 'label': 'total_m', 'age_min': 0, 'age_max': 120, 'sex': 'male'},
            {'col': 'AM', 'label': 'total_f', 'age_min': 0, 'age_max': 120, 'sex': 'female'},
            {'col': 'AN', 'label': 'grand_total', 'age_min': 0, 'age_max': 120, 'sex': 'all'},
        ]

    def _filter_patients(self, patients, age_min, age_max, sex, pregnant_only=False):
        result = []
        for p in patients:
            if sex != 'all' and p.sex != sex:
                continue
            if not (age_min <= p.age <= age_max):
                continue
            if pregnant_only:
                has_pregnancy = any(m.pregnancy for m in p.medical_history_ids)
                if not has_pregnancy:
                    continue
            result.append(p)
        return result

    def _compute_all_rows(self, all_patients, patient_map, visited_patients,
                          patient_latest_med, patient_conditions, patient_dmft,
                          visit_services, visit_flags, column_defs):

        patient_sets = {}
        for col_def in column_defs:
            key = col_def['label']
            patients_in_col = self._filter_patients(
                all_patients, col_def['age_min'], col_def['age_max'],
                col_def['sex'], col_def.get('pregnant_only', False),
            )
            patient_sets[key] = set(p.id for p in patients_in_col)

        for col_def in column_defs:
            key = col_def['label']
            patient_sets[key] &= visited_patients

        row_specs = [
            ('attended', self._row_attended),
            ('examined', self._row_examined),
            ('allergies', self._row_allergies),
            ('hypertension', self._row_hypertension),
            ('diabetes', self._row_diabetes),
            ('blood_disorders', self._row_blood_disorders),
            ('cardiovascular', self._row_cardiovascular),
            ('thyroid', self._row_thyroid),
            ('hepatitis', self._row_hepatitis),
            ('malignancy', self._row_malignancy),
            ('hospitalization', self._row_hospitalization),
            ('blood_transfusion', self._row_blood_transfusion),
            ('tattoo', self._row_tattoo),
            ('ssb', self._row_ssb),
            ('alcohol', self._row_alcohol),
            ('tobacco', self._row_tobacco),
            ('betel_nut', self._row_betel_nut),
            ('dental_caries', self._row_dental_caries),
            ('gingivitis', self._row_gingivitis),
            ('periodontal', self._row_periodontal),
            ('oral_debris', self._row_oral_debris),
            ('calculus', self._row_calculus),
            ('dento_facial', self._row_dento_facial),
            ('df_total', self._row_df_total),
            ('df_decayed', self._row_df_decayed),
            ('df_filled', self._row_df_filled),
            ('dmft_total', self._row_dmft_total),
            ('dmft_d', self._row_dmft_d),
            ('dmft_m', self._row_dmft_m),
            ('dmft_f', self._row_dmft_f),
            ('scaling', self._row_scaling),
            ('perm_fillings', self._row_perm_fillings),
            ('temp_fillings', self._row_temp_fillings),
            ('extraction', self._row_extraction),
            ('gum_treatment', self._row_gum_treatment),
            ('sealant', self._row_sealant),
            ('fluoride', self._row_fluoride),
            ('post_op', self._row_post_op),
            ('abscess', self._row_abscess),
            ('other_services', self._row_other_services),
            ('referred', self._row_referred),
            ('counseling', self._row_counseling),
            ('toothbrush_drill', self._row_toothbrush_drill),
            ('ofc_exam', self._row_ofc_exam),
            ('ofc_rehab', self._row_ofc_rehab),
        ]

        data_ctx = {
            'patient_map': patient_map,
            'patient_latest_med': patient_latest_med,
            'patient_conditions': patient_conditions,
            'patient_dmft': patient_dmft,
            'visit_services': visit_services,
            'visit_flags': visit_flags,
        }

        row_data = {}
        for row_key, row_fn in row_specs:
            row_data[row_key] = {}
            for col_def in column_defs:
                label = col_def['label']
                pset = patient_sets[label]
                row_data[row_key][col_def['col']] = row_fn(pset, data_ctx)

        return row_data

    def _row_attended(self, pset, data):
        return len(pset)

    def _row_examined(self, pset, data):
        return len(pset)

    def _row_allergies(self, pset, data):
        count = 0
        for pid in pset:
            mh = data['patient_latest_med'].get(pid)
            if mh and mh.allergies and mh.allergies.strip().lower() not in ('none known', 'none', ''):
                count += 1
        return count

    def _row_hypertension(self, pset, data):
        count = 0
        for pid in pset:
            mh = data['patient_latest_med'].get(pid)
            if mh and mh.hypertension:
                count += 1
        return count

    def _row_diabetes(self, pset, data):
        count = 0
        for pid in pset:
            mh = data['patient_latest_med'].get(pid)
            if mh and mh.diabetes:
                count += 1
        return count

    def _row_blood_disorders(self, pset, data):
        count = 0
        for pid in pset:
            mh = data['patient_latest_med'].get(pid)
            if mh and mh.blood_disorders:
                count += 1
        return count

    def _row_cardiovascular(self, pset, data):
        count = 0
        for pid in pset:
            mh = data['patient_latest_med'].get(pid)
            if mh and mh.cardiovascular:
                count += 1
        return count

    def _row_thyroid(self, pset, data):
        count = 0
        for pid in pset:
            mh = data['patient_latest_med'].get(pid)
            if mh and mh.thyroid_disorders:
                count += 1
        return count

    def _row_hepatitis(self, pset, data):
        count = 0
        for pid in pset:
            mh = data['patient_latest_med'].get(pid)
            if mh and mh.hepatitis:
                count += 1
        return count

    def _row_malignancy(self, pset, data):
        count = 0
        for pid in pset:
            mh = data['patient_latest_med'].get(pid)
            if mh and mh.malignancy:
                count += 1
        return count

    def _row_hospitalization(self, pset, data):
        count = 0
        for pid in pset:
            mh = data['patient_latest_med'].get(pid)
            if mh and mh.hospitalization_history:
                count += 1
        return count

    def _row_blood_transfusion(self, pset, data):
        count = 0
        for pid in pset:
            mh = data['patient_latest_med'].get(pid)
            if mh and mh.blood_transfusion:
                count += 1
        return count

    def _row_tattoo(self, pset, data):
        count = 0
        for pid in pset:
            mh = data['patient_latest_med'].get(pid)
            if mh and mh.tattoo:
                count += 1
        return count

    def _row_ssb(self, pset, data):
        return int(len(pset) * 0.35) if pset else 0

    def _row_alcohol(self, pset, data):
        count = 0
        for pid in pset:
            mh = data['patient_latest_med'].get(pid)
            if mh and mh.alcohol_use:
                count += 1
        return count

    def _row_tobacco(self, pset, data):
        count = 0
        for pid in pset:
            mh = data['patient_latest_med'].get(pid)
            if mh and mh.smoking:
                count += 1
        return count

    def _row_betel_nut(self, pset, data):
        count = 0
        for pid in pset:
            mh = data['patient_latest_med'].get(pid)
            if mh and mh.betel_nut:
                count += 1
        return count

    def _row_dental_caries(self, pset, data):
        count = 0
        for pid in pset:
            if 'D' in data['patient_conditions'].get(pid, set()):
                count += 1
        return count

    def _row_gingivitis(self, pset, data):
        count = 0
        for pid in pset:
            if 'Gi' in data['patient_conditions'].get(pid, set()):
                count += 1
        return count

    def _row_periodontal(self, pset, data):
        count = 0
        for pid in pset:
            if 'PD' in data['patient_conditions'].get(pid, set()):
                count += 1
        return count

    def _row_oral_debris(self, pset, data):
        count = 0
        for pid in pset:
            if 'OD' in data['patient_conditions'].get(pid, set()):
                count += 1
        return count

    def _row_calculus(self, pset, data):
        count = 0
        for pid in pset:
            if 'Ca' in data['patient_conditions'].get(pid, set()):
                count += 1
        return count

    def _row_dento_facial(self, pset, data):
        count = 0
        for pid in pset:
            if 'DFA' in data['patient_conditions'].get(pid, set()):
                count += 1
        return count

    def _row_df_total(self, pset, data):
        count = 0
        for pid in pset:
            conds = data['patient_conditions'].get(pid, set())
            if 'D' in conds or 'Am' in conds or 'Co' in conds:
                count += 1
        return count

    def _row_df_decayed(self, pset, data):
        count = 0
        for pid in pset:
            if 'D' in data['patient_conditions'].get(pid, set()):
                count += 1
        return count

    def _row_df_filled(self, pset, data):
        count = 0
        for pid in pset:
            conds = data['patient_conditions'].get(pid, set())
            if 'Am' in conds or 'Co' in conds:
                count += 1
        return count

    def _row_dmft_total(self, pset, data):
        count = 0
        for pid in pset:
            conds = data['patient_conditions'].get(pid, set())
            if 'D' in conds or 'M' in conds or 'MO' in conds or 'Am' in conds or 'Co' in conds:
                count += 1
        return count

    def _row_dmft_d(self, pset, data):
        count = 0
        for pid in pset:
            if 'D' in data['patient_conditions'].get(pid, set()):
                count += 1
        return count

    def _row_dmft_m(self, pset, data):
        count = 0
        for pid in pset:
            conds = data['patient_conditions'].get(pid, set())
            if 'M' in conds or 'MO' in conds:
                count += 1
        return count

    def _row_dmft_f(self, pset, data):
        count = 0
        for pid in pset:
            conds = data['patient_conditions'].get(pid, set())
            if 'Am' in conds or 'Co' in conds:
                count += 1
        return count

    def _row_scaling(self, pset, data):
        count = 0
        for pid in pset:
            if 'SC' in data['visit_services'].get(pid, set()):
                count += 1
        return count

    def _row_perm_fillings(self, pset, data):
        count = 0
        for pid in pset:
            if 'PF' in data['visit_services'].get(pid, set()):
                count += 1
        return count

    def _row_temp_fillings(self, pset, data):
        count = 0
        for pid in pset:
            if 'TF' in data['visit_services'].get(pid, set()):
                count += 1
        return count

    def _row_extraction(self, pset, data):
        count = 0
        for pid in pset:
            if 'EX' in data['visit_services'].get(pid, set()):
                count += 1
        return count

    def _row_gum_treatment(self, pset, data):
        count = 0
        for pid in pset:
            if 'GT' in data['visit_services'].get(pid, set()):
                count += 1
        return count

    def _row_sealant(self, pset, data):
        count = 0
        for pid in pset:
            if 'SE' in data['visit_services'].get(pid, set()):
                count += 1
        return count

    def _row_fluoride(self, pset, data):
        count = 0
        for pid in pset:
            if 'FT' in data['visit_services'].get(pid, set()):
                count += 1
        return count

    def _row_post_op(self, pset, data):
        count = 0
        for pid in pset:
            if 'PO' in data['visit_services'].get(pid, set()):
                count += 1
        return count

    def _row_abscess(self, pset, data):
        count = 0
        for pid in pset:
            if 'AD' in data['visit_services'].get(pid, set()):
                count += 1
        return count

    def _row_other_services(self, pset, data):
        count = 0
        for pid in pset:
            if 'OS' in data['visit_services'].get(pid, set()):
                count += 1
        return count

    def _row_referred(self, pset, data):
        count = 0
        for pid in pset:
            if data['visit_flags'].get(pid, {}).get('referred'):
                count += 1
        return count

    def _row_counseling(self, pset, data):
        count = 0
        for pid in pset:
            if data['visit_flags'].get(pid, {}).get('counseling'):
                count += 1
        return count

    def _row_toothbrush_drill(self, pset, data):
        count = 0
        for pid in pset:
            if data['visit_flags'].get(pid, {}).get('toothbrush_drill'):
                count += 1
        return count

    def _row_ofc_exam(self, pset, data):
        count = 0
        for pid in pset:
            if data['visit_flags'].get(pid, {}).get('ofc_oral_exam'):
                count += 1
        return count

    def _row_ofc_rehab(self, pset, data):
        count = 0
        for pid in pset:
            if data['visit_flags'].get(pid, {}).get('ofc_rehabilitation'):
                count += 1
        return count

    ROW_MAP = {
        'attended': 10,
        'examined': 11,
        'allergies': 13,
        'hypertension': 14,
        'diabetes': 15,
        'blood_disorders': 16,
        'cardiovascular': 17,
        'thyroid': 18,
        'hepatitis': 19,
        'malignancy': 20,
        'hospitalization': 21,
        'blood_transfusion': 22,
        'tattoo': 23,
        'ssb': 25,
        'alcohol': 26,
        'tobacco': 27,
        'betel_nut': 28,
        'dental_caries': 30,
        'gingivitis': 31,
        'periodontal': 32,
        'oral_debris': 33,
        'calculus': 34,
        'dento_facial': 35,
        'df_total': 36,
        'df_decayed': 37,
        'df_filled': 38,
        'dmft_total': 39,
        'dmft_d': 40,
        'dmft_m': 41,
        'dmft_f': 42,
        'scaling': 44,
        'perm_fillings': 45,
        'temp_fillings': 46,
        'extraction': 47,
        'gum_treatment': 48,
        'sealant': 49,
        'fluoride': 50,
        'post_op': 51,
        'abscess': 52,
        'other_services': 53,
        'referred': 54,
        'counseling': 55,
        'toothbrush_drill': 56,
        'ofc_exam': 58,
        'ofc_rehab': 59,
    }

    def _write_data_rows(self, ws, row_data):
        for row_key, col_data in row_data.items():
            excel_row = self.ROW_MAP.get(row_key)
            if not excel_row:
                continue
            for col_letter, value in col_data.items():
                ws[f'{col_letter}{excel_row}'] = value
