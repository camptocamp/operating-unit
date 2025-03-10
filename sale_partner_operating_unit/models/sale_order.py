# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _compute_field_value(self, field):
        # OVERRIDE: each time the ``operating_unit_id`` field is recomputed,
        # we flush the ``operating_unit_ids`` field of the partner.
        if field.name == "operating_unit_id":
            self.partner_id.flush_recordset(fnames=["operating_unit_ids"])
        return super()._compute_field_value(field)

    @api.depends("partner_id", "partner_id.operating_unit_ids", "team_id")
    def _compute_operating_unit_id(self):
        # For orders without a team, use the partner's ``operating_unit_ids``
        # if exactly one is set.
        if orders_without_team := self.filtered(lambda order: not order.team_id):
            for order in orders_without_team:
                if len(order.partner_id.operating_unit_ids) == 1:
                    order.operating_unit_id = order.partner_id.operating_unit_ids
                else:
                    order.operating_unit_id = False
        else:
            # For orders with a team, let the super method compute the operating unit.
            return super(
                SaleOrder, self - orders_without_team
            )._compute_operating_unit_id()
