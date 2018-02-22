# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.tests.common import SavepointCase


class TestOperatiingUnitUserId(SavepointCase):

    def setUp(self):
        super().setUp()

        self.ou1 = self.env.ref('operating_unit.b2c_operating_unit')
        self.ou2 = self.env.ref('operating_unit.b2b_operating_unit')

        self.user1 = self.env['res.users'].create({
            'name': 'User 1',
            'login': 'user1',
            'operating_unit_ids': [(4, self.ou1.id)]
        })

        self.user2 = self.env['res.users'].create({
            'name': 'User 2',
            'login': 'user2',
            'operating_unit_ids': [(4, self.ou2.id)]
        })

        self.user3 = self.env['res.users'].create({
            'name': 'User 3',
            'login': 'user3',
            'operating_unit_ids': [(4, self.ou1.id), (4, self.ou2.id)]
        })

        self.event1 = self.env['event.event'].create({
            'name': 'Testevent',
            'operating_unit_id': self.ou1.id,
            'date_begin': '2018-03-01 10:00:00',
            'date_end': '2018-03-01 11:00:00'
        })

        self.event2 = self.env['event.event'].create({
            'name': 'Testevent',
            'operating_unit_id': self.ou2.id,
            'date_begin': '2018-03-01 10:00:00',
            'date_end': '2018-03-01 11:00:00'
        })

    def test_compute(self):
        res = self.event1.operating_unit_user_ids
        self.assertEqual(len(res), 3)
        logins = [item.login for item in res]
        self.assertIn(self.user1.login, logins)
        self.assertIn(self.user3.login, logins)
        self.assertNotIn(self.user2.login, logins)

        res = self.event2.operating_unit_user_ids
        self.assertEqual(len(res), 3)
        logins = [item.login for item in res]
        self.assertIn(self.user2.login, logins)
        self.assertIn(self.user3.login, logins)
        self.assertNotIn(self.user1.login, logins)

    def test_search(self):
        res1 = self.event1._search_operating_unit_user_ids(
            'in',
            [self.user1.id]
        )
        res2 = self.event1._search_operating_unit_user_ids(
            'in',
            [self.user2.id]
        )
        res3 = self.event1._search_operating_unit_user_ids(
            'in',
            [self.user3.id]
        )

        self.assertEqual(len(res1[0][2]), 1)
        self.assertEqual(len(res2[0][2]), 1)
        self.assertEqual(len(res3[0][2]), 2)

        self.assertEqual(res1[0][2][0], self.ou1.id)
        self.assertEqual(res2[0][2][0], self.ou2.id)
        self.assertIn(self.ou1.id, res3[0][2])
        self.assertIn(self.ou2.id, res3[0][2])
