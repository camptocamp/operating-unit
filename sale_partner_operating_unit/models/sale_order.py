# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends("partner_id.operating_unit_ids")
    def _compute_team_id(self):
        # For orders without a team, if the partner's ``operating_unit_ids``
        # is set exactly one, we skip the computation of the team.
        skip_teams_sales = self.filtered(
            lambda order: not order.team_id
            and order.partner_id.operating_unit_ids
            and (len(order.partner_id.operating_unit_ids) == 1)
        )
        if skip_teams_sales:
            self = self - skip_teams_sales
        return super()._compute_team_id()

    @api.depends("team_id", "partner_id.operating_unit_ids")
    def _compute_operating_unit_id(self):
        # For orders without a team, use the partner's ``operating_unit_ids``
        # if exactly one is set.
        if orders_without_team := self.filtered(lambda order: not order.team_id):
            for order in orders_without_team:
                if len(order.partner_id.operating_unit_ids) == 1:
                    order.operating_unit_id = order.partner_id.operating_unit_ids
                else:
                    order.operating_unit_id = False

        # For orders with a team, let the super method compute the operating unit.
        return super(SaleOrder, self - orders_without_team)._compute_operating_unit_id()
