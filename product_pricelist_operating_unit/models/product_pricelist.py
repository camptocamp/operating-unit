# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    operating_unit_id = fields.Many2one(
        "operating.unit",
        default=lambda self: self.env["res.users"]._get_default_operating_unit(),
        check_company=True,
    )
