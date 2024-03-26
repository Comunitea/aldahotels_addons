from odoo import _, api, fields, models
from odoo.tools.misc import clean_context
from odoo.tests.common import Form
from odoo.exceptions import UserError

class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    service_line_ids = fields.One2many('pms.service.line', 'invoice_line_id', string="Service lines")


class AccountMove(models.Model):

    _inherit = "account.move"

    def _prepare_invoice_data(self, dest_company):
        self.ensure_one()
        vals = super(AccountMove, self)._prepare_invoice_data(dest_company)
        hotel = self.env["pms.property"].search(
            [("partner_id", "=", self.commercial_partner_id.id),('company_id','!=',self.env.company.id)], limit=1
        )

        dest_journal_type = self._get_destination_journal_type()
        dest_journal = self.env["account.journal"]
        tpv = self.env['pos.config'].search([('company_id','=',dest_company.id)],limit=1)
        if tpv:
            dest_journal = tpv.invoice_journal_id
        if not dest_journal:
            if not hotel:
                dest_journal = self.env["account.journal"].search(
                    [("type", "=", dest_journal_type), ("company_id", "=", dest_company.id),("pms_property_ids",'=',False)],
                    limit=1,
                )
            else:
                dest_journal = self.env["account.journal"].search(
                    [("type", "=", dest_journal_type), ("company_id", "=", dest_company.id),("pms_property_ids",'=',hotel.id)],
                    limit=1,
                )
            if not dest_journal:
                raise UserError(
                    _('Please define %s journal for this company: "%s" (id:%d).')
                    % (dest_journal_type, dest_company.name, dest_company.id)
                )

        partner_id = self.company_id.partner_id
        if dest_journal_type in ['out_invoice','out_refund'] and self.pms_property_id:
            partner_id = self.pms_property_id.partner_id
        vals.update(
            {
                "journal_id": dest_journal.id,
                "partner_id": partner_id.id,
            }
        )
        return vals

    def _find_company_from_invoice_partner(self):
        self.ensure_one()
        hotel = self.env["pms.property"].search(
            [("partner_id", "=", self.commercial_partner_id.id),('company_id','!=',self.env.company.id)], limit=1
        )
        if not hotel or not hotel.company_id:
            return super(AccountMove, self)._find_company_from_invoice_partner()
        else:
            return hotel.company_id
