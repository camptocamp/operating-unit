# © 2017 Niaga Solution - Edi Santoso <repodevs@gmail.com>
# Copyright (C) 2020 Serpent Consulting Services
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import Command
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestResPartnerOperatingUnit(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.res_partner_model = cls.env["res.partner"]
        cls.res_users_model = cls.env["res.users"]
        # Company
        cls.company = cls.env.ref("base.main_company")
        # Main Operating Unit
        cls.ou1 = cls.env.ref("operating_unit.main_operating_unit")
        # B2C Operating Unit
        cls.b2c = cls.env.ref("operating_unit.b2c_operating_unit")

        # Create User 1 with Main OU
        cls.user1 = cls._create_user("user_1", cls.company, cls.ou1)
        # Create User 2 with B2C OU
        cls.user2 = cls._create_user("user_2", cls.company, cls.b2c)

        # Create Partner 1 with Main OU
        cls.partner1 = cls._create_partner("Test Partner 1", cls.ou1)

        # Create Partner 2 with B2C OU
        cls.partner2 = cls._create_partner("Test Partner 2", cls.b2c)

    @classmethod
    def _create_partner(cls, name, operating_unit, context=None):
        """Create a partner."""
        partner = cls.res_partner_model.create(
            {"name": name, "operating_unit_ids": [Command.link(operating_unit.id)]}
        )
        return partner

    @classmethod
    def _create_user(cls, login, company, operating_units, context=None):
        """Create a user."""
        user = cls.res_users_model.create(
            {
                "name": "Test User",
                "login": login,
                "password": "demo",
                "email": "test@yourcompany.com",
                "company_id": company.id,
                "company_ids": [Command.link(company.id)],
                "operating_unit_ids": [Command.link(ou.id) for ou in operating_units],
            }
        )
        return user

    def _update_user(self, user, operating_units, context=None):
        with self.assertRaises(UserError):
            user.write(
                {
                    "default_operating_unit_id": [
                        [Command.link(ou.id) for ou in operating_units],
                    ]
                }
            )

    def test_01_operating_unit(self):
        """Test Operating Unit."""
        self.assertEqual(self.user1.default_operating_unit_id, self.ou1)
        self.assertEqual(self.user2.default_operating_unit_id, self.ou1)

        self._update_user(self.user1, self.b2c)
        self._update_user(self.user2, self.ou1)

        self.assertEqual(self.partner1.operating_unit_ids, self.ou1)
        self.assertEqual(self.partner2.operating_unit_ids, self.b2c)
