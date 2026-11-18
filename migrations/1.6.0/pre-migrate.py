"""Retire the legacy dental.history model.

``dental.tooth.surface`` replaced it long ago (the patient form and the portal
already read the odontogram), but its views, ACLs and table were left behind.
This drops the leftovers so the model can be removed from the addon cleanly.
"""
import logging

from odoo.tools.sql import table_exists

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    _logger.info("obbs_dental: retiring the dental.history model")

    # XML/DB artefacts that reference the removed model
    cr.execute("""
        DELETE FROM ir_ui_view
         WHERE model = 'dental.history'
            OR id IN (SELECT res_id FROM ir_model_data
                       WHERE module = 'obbs_dental' AND model = 'ir.ui.view'
                         AND name IN ('view_dental_history_list', 'view_dental_history_form'))
    """)
    cr.execute("""
        DELETE FROM ir_act_window
         WHERE res_model = 'dental.history'
            OR id IN (SELECT res_id FROM ir_model_data
                       WHERE module = 'obbs_dental' AND model = 'ir.actions.act_window'
                         AND name = 'action_dental_history')
    """)
    cr.execute("""
        DELETE FROM ir_model_access
         WHERE model_id IN (SELECT id FROM ir_model WHERE model = 'dental.history')
    """)
    cr.execute("""
        DELETE FROM ir_model_data
         WHERE module = 'obbs_dental'
           AND name IN ('view_dental_history_list', 'view_dental_history_form',
                        'action_dental_history',
                        'access_dental_history_manager', 'access_dental_history_assistant')
    """)

    if table_exists(cr, 'dental_history'):
        cr.execute("DROP TABLE dental_history CASCADE")
        _logger.info("obbs_dental: dropped table dental_history")
