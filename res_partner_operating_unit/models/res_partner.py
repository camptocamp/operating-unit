# © 2017 Niaga Solution - EdiAntoso <repodevs@gmail.com>
# Copyright (C) 2019 Serpent Consulting Services
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.fields import Domain


class ResPartner(models.Model):
    _inherit = "res.partner"

    operating_unit_ids = fields.Many2many(
        comodel_name="operating.unit",
        relation="operating_unit_partner_rel",
        column1="partner_id",
        column2="operating_unit_id",
        string="Operating Units",
    )

    def write(self, vals):
        result = super().write(vals)
        if "operating_unit_ids" in vals:
            for partner in self:
                if partner.user_ids:
                    assigned_operating_units = set(
                        user.assigned_operating_unit_ids for user in partner.user_ids
                    )
                    if (
                        len(assigned_operating_units) > 1
                        or partner.operating_unit_ids not in assigned_operating_units
                    ):
                        raise UserError(
                            self.env._(
                                "The operating units of the partner are not compatible "
                                "with the operating units of the related user(s)."
                            )
                        )
        return result

    @api.model
    def _user_ous_domain(self):
        ou_ids = self.env.user.operating_unit_ids.ids
        domain = Domain.OR(
            [
                Domain("operating_unit_ids", "in", ou_ids),
                Domain("operating_unit_ids", "=", False),
            ]
        )
        return domain

    # Extending methods to replace a record rule.
    # Ref: https://github.com/OCA/operating-unit/issues/258
    @api.model
    def search(self, args, offset=0, limit=None, order=None):
        # Get the OUs of the user
        domain = self._user_ous_domain()
        return super().search(domain + args, offset=offset, limit=limit, order=order)

    @api.model
    def search_count(self, args, limit=None):
        # Get the OUs of the user
        domain = self._user_ous_domain()
        return super().search_count(domain + args, limit=limit)
