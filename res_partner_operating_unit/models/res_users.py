# © 2017 Niaga Solution - Edi Santoso <repodevs@gmail.com>
# Copyright (C) 2019 Serpent Consulting Services
# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import api, models
from odoo.exceptions import UserError
from odoo.fields import Command


class ResUsers(models.Model):
    _inherit = "res.users"

    def _sync_partner_operating_units(self):
        for user in self:
            if user.assigned_operating_unit_ids != user.partner_id.operating_unit_ids:
                user.partner_id.write(
                    {
                        "operating_unit_ids": [
                            Command.set(user.assigned_operating_unit_ids.ids)
                        ]
                    }
                )

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        for user in users:
            if (
                user.partner_id.operating_unit_ids
                and user.partner_id.operating_unit_ids
                != user.assigned_operating_unit_ids
            ):
                raise UserError(
                    self.env._(
                        "Cannot create user '%(user)s': partner '%(partner)s'"
                        " already has operating units %(partner_ous)s,"
                        " which differ from %(user_ous)s.",
                        user=user.display_name,
                        partner=user.partner_id.display_name,
                        partner_ous=user.partner_id.operating_unit_ids.mapped("name"),
                        user_ous=user.assigned_operating_unit_ids.mapped("name"),
                    )
                )
            else:
                user._sync_partner_operating_units()
        return users

    def write(self, vals):
        res = super().write(vals)
        if "assigned_operating_unit_ids" in vals:
            for user in self:
                user._sync_partner_operating_units()
        return res
