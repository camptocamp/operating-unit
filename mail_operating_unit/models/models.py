# Copyright 2024 Camptocamp SA
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, models


class BaseModel(models.AbstractModel):
    _inherit = "base"

    @api.model
    def _mail_get_operating_unit(self):
        return (
            self.operating_unit_id
            if "operating_unit_id" in self and self.operating_unit_id
            else False
        )

    def _mail_get_operating_units(self):
        self.ensure_one()
        operating_unit = self._mail_get_operating_unit()
        if operating_unit:
            return operating_unit

        user = self.env.user
        user_operating_units = user.operating_unit_ids
        if user_operating_units:
            if len(user_operating_units) == 1:
                return user_operating_units
            unique_alias_domains = user_operating_units.mapped("alias_domain_id.id")
            if len(user_operating_units) > 1 and len(unique_alias_domains) == 1:
                return user_operating_units[0]
        return False

    def _mail_get_alias_domains(self, default_company=False):
        alias_domains = super()._mail_get_alias_domains(default_company=default_company)

        return {
            record.id: (
                record._mail_get_operating_units().alias_domain_id
                if record._mail_get_operating_units()
                else alias_domains[record.id]
            )
            for record in self
        }
