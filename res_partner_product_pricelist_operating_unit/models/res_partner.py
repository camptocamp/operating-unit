# 2025 Camptocamp SA (https://www.camptocamp.com).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import _, api, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.depends("operating_unit_ids")
    def _compute_product_pricelist(self):
        return super()._compute_product_pricelist()

    def _check_pricelist_operating_unit(self):
        for partner in self:
            pricelist = partner.property_product_pricelist
            if (
                pricelist
                and pricelist.operating_unit_id not in partner.operating_unit_ids
            ):
                raise ValidationError(
                    _(
                        "Pricelist '%(pricelist)s' belongs to "
                        "Operating Unit '%(operating_unit)s' "
                        "which is not associated to this partner.",
                        pricelist=pricelist.name,
                        operating_unit=pricelist.operating_unit_id.name,
                    )
                )

    def write(self, vals):
        res = super().write(vals)
        # We check that both `operating_unit_ids` and `property_product_pricelist`
        # are in `vals` to avoid wrongly raised ValidationError
        if "operating_unit_ids" in vals and "property_product_pricelist" in vals:
            self._check_pricelist_operating_unit()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        partners = super().create(vals_list)
        for partner, vals in zip(partners, vals_list, strict=True):
            if "operating_unit_ids" in vals and "property_product_pricelist" in vals:
                partner._check_pricelist_operating_unit()
        return partners
