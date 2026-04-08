# Copyright 2026 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    operating_unit_use_mail_server = fields.Boolean(
        string="Use operating unit outgoing mail server",
        config_parameter="mail_operating_unit.operating_unit_use_mail_server",
        help=(
            "When enabled, the outgoing mail server is automatically selected "
            "from the operating unit, unless the email template already defines one."
        ),
    )
