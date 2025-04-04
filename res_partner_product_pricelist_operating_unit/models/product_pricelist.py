# 2025 Camptocamp SA (https://www.camptocamp.com).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import api, models


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    @api.model
    def _get_partner_pricelist_multi(self, partner_ids):
        # OVERRIDE:
        # super() returns a dict { partner_id: product.pricelist() }
        res = super()._get_partner_pricelist_multi(partner_ids)
        Pricelist = self.env["product.pricelist"]

        for partner_id, pricelist in res.items():
            partner = self.env["res.partner"].browse(partner_id)
            if (
                partner.operating_unit_ids
                and pricelist.operating_unit_id not in partner.operating_unit_ids
            ):
                domain = self._get_partner_pricelist_operating_unit_domain(partner)
                alternative_pricelist = Pricelist.search(domain, limit=1)
                res[partner_id] = alternative_pricelist

        return res

    def _get_partner_pricelist_operating_unit_domain(self, partner):
        return [
            ("active", "=", True),
            ("company_id", "in", [self.env.company.id, False]),
            "|",
            ("operating_unit_id", "in", partner.operating_unit_ids.ids),
            ("operating_unit_id", "=", False),
        ]
