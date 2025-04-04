# 2025 Camptocamp SA (https://www.camptocamp.com).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.depends("operating_unit_ids")
    def _compute_product_pricelist(self):
        return super()._compute_product_pricelist()
