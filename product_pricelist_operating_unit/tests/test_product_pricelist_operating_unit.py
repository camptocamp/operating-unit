# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.base.tests.common import BaseCommon


class TestProductPricelistOperatingUnit(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.res_users_model = cls.env["res.users"]
        cls.product_pricelist_model = cls.env["product.pricelist"]
        # Groups
        cls.grp_system = cls.env.ref("base.group_system")
        cls.grp_user = cls.env.ref("operating_unit.group_multi_operating_unit")
        # Company
        cls.company = cls.env.ref("base.main_company")
        # Main Operating Unit
        cls.ou1 = cls.env.ref("operating_unit.main_operating_unit")
        # B2C Operating Unit
        cls.b2c = cls.env.ref("operating_unit.b2c_operating_unit")
        # Create User 1 with Main OU

        cls.user1 = cls._create_user(
            "user_1", [cls.grp_system, cls.grp_user], cls.company, [cls.ou1]
        )
        # Create User 2 with B2C OU
        cls.user2 = cls._create_user(
            "user_2", [cls.grp_system, cls.grp_user], cls.company, [cls.b2c]
        )
        # Create Product Pricelists
        cls.pricelist1 = cls._create_product_pricelist(cls.user1.id, cls.ou1)
        cls.pricelist2 = cls._create_product_pricelist(cls.user2.id, cls.b2c)

    @classmethod
    def _create_user(cls, login, groups, company, operating_units, context=None):
        """Create a user."""
        group_ids = [group.id for group in groups]
        user = cls.res_users_model.create(
            {
                "name": "Test User",
                "login": login,
                "password": "demo",
                "email": "test@yourcompany.com",
                "company_id": company.id,
                "company_ids": [(4, company.id)],
                "operating_unit_ids": [(4, ou.id) for ou in operating_units],
                "groups_id": [(6, 0, group_ids)],
            }
        )
        return user

    @classmethod
    def _create_product_pricelist(cls, uid, operating_unit):
        """Create a Product Pricelist."""
        pricelist = cls.product_pricelist_model.with_user(uid).create(
            {
                "name": "Product Pricelist",
                "operating_unit_id": operating_unit.id,
                "company_id": cls.company.id,
            }
        )
        return pricelist

    def test_product_pricelist(self):
        # User 2 is only assigned to B2C Operating Unit, and cannot
        # access Product Pricelist for Main Operating Unit.
        pricelist = self.product_pricelist_model.with_user(self.user2.id).search(
            [("id", "=", self.pricelist1.id), ("operating_unit_id", "=", self.ou1.id)]
        )
        self.assertEqual(
            pricelist.ids, [], "User 2 should not have access to " "%s" % self.ou1.name
        )
