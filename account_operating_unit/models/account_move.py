# -*- coding: utf-8 -*-
# © 2015 Eficent - Jordi Ballester Alomar
# © 2015 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from openerp.tools.translate import _
from openerp import api, fields, models
from openerp.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model
    def _query_get(self, domain=None):
        if self._context.get('operating_unit_ids', False):
            domain.append(('operating_unit_id', 'in',
                           self._context.get('operating_unit_ids')))
        return super(AccountMoveLine, self)._query_get(domain)

    operating_unit_id = fields.Many2one('operating.unit', 'Operating Unit',
                        default=lambda self: self.env[
                        'res.users'].operating_unit_default_get(
                        self._uid))
    ou_cleared_line_id = fields.Many2one('account.move.line',
                                              'Inter-OU Cleared move line')

    @api.one
    @api.constrains('operating_unit_id', 'company_id')
    def _check_company_operating_unit(self):
        if self.company_id and self.operating_unit_id and\
        self.company_id != self.operating_unit_id.company_id:
            raise UserError(_('Configuration error!\nThe Company in the\
            Move Line and in the Operating Unit must be the same.'))


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.multi
    def post(self):
        ml_obj = self.env['account.move.line']
        for move in self:
            # If all move lines point to the same operating unit, there's no
            # need to create a balancing move line
#            ou_list_ids = [line.operating_unit_id and
#                           line.operating_unit_id.id for line in
#                           move.line_ids]
#            ou_ids = list(set(ou_list_ids))
#            if len(ou_ids) <= 1:
#                continue

            ou_list_ids = ml_obj.read_group([('move_id', '=', move.id)],
                                            ['operating_unit_id'],
                                            ['operating_unit_id'])
            if len(ou_list_ids) <= 1:
                continue
            lines = []
            for line in move.line_ids:
                cleared = False
                operating_unit = line.operating_unit_id
                if operating_unit:
                    cl_acc = line.company_id.inter_ou_clearing_account_id
                    if not cl_acc:
                        raise UserError(_('Configuration error!\n\
                        You need to define an inter-operating unit clearing\
                        account in the company settings.'))
                    if line.account_id == cl_acc:
                        continue
                    # Check if this line has already been cleared
                    for l in move.line_ids:
                        if line == l.ou_cleared_line_id:
                            cleared = True
                    if cleared:
                        continue

                    # Create a balancing move line in the operating unit
                    # clearing account
                    line_vals = {
                        'name': line.name,
                        'partner_id': line.partner_id and
                        line.partner_id.id or False,
                        'account_id': cl_acc.id,
                        'move_id': line.move_id.id,
                        'journal_id': line.journal_id.id,
                        'date': line.date,
                        'debit': line.credit,
                        'credit': line.debit,
                        'currency_id': line.currency_id.id,
                        'amount_currency': line.amount_currency,
                        'operating_unit_id': operating_unit.id,
                        'analytic_account_id': line.analytic_account_id.id,
                        'ou_cleared_line_id': line.id,
                    }
                    lines.append((0, 0, line_vals))
            move.write({'line_ids': lines})
        return super(AccountMove, self).post()

    @api.one
    @api.constrains('line_ids')
    def _check_same_ou_dr_cr(self):
        dr = {}
        cr = {}
        ou_ids = []
        for line in self.line_ids:
            operating_unit_id = line.operating_unit_id and\
                                line.operating_unit_id.id
            if operating_unit_id:
                cl_acc = line.company_id.inter_ou_clearing_account_id
                if not cl_acc:
                    raise UserError(_('Configuration error!\n\
                    You need to define an inter-operating\
                    unit clearing account in the company settings.'))
                ou_ids.append(operating_unit_id)
                if not cl_acc:
                    if operating_unit_id in dr:
                        dr[operating_unit_id] += line.debit
                    else:
                        dr[operating_unit_id] = line.debit

                    if operating_unit_id in cr:
                        cr[operating_unit_id] += line.credit
                    else:
                        cr[operating_unit_id] = line.credit
        for ou_id in ou_ids:
            if (
                ou_id in dr and
                ou_id in cr and
                dr[ou_id] > 0 and
                cr[ou_id] > 0
            ):
                raise UserError(_('Configuration error!\nThe same\
                operating unit cannot exist in the debit and credit\
                for the same account.'))
