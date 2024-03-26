from odoo import _, api, fields, models
from odoo.exceptions import UserError


class WzdIntercompanyRegularization(models.TransientModel):

    _name = "wzd.intercompany.regularization"
    from_date = fields.Date(help="Empty from the beginning of time")
    to_date = fields.Date(default=fields.Date.today)
    service_line_ids = fields.Many2many(
        "pms.service.line", string="Service lines to regularize"
    )

    def action_regularize(self):
        tpvs = self.sudo().env['pos.config'].search([('company_id','!=',self.env.company.id)])
        hotels = tpvs.mapped('reservation_allowed_propertie_ids').filtered(lambda x: x.company_id == self.env.company)

        domain = [('pms_property_id','in', hotels.ids),('regularize_state','=','to_regularize')]
        if self.from_date:
            domain.append(('date', '>=', self.from_date))
        if self.to_date:
            domain.append(('date', '<=', self.to_date))

        if not hotels:
            raise UserError(_("No hotels to regularize"))

        services = self.env['pms.service.line'].search(domain)
        if not services:
            raise UserError(_("No service lines to regularize"))

        to_regularize = services.filtered(lambda x: x.product_id.available_in_pos and all([y.company_id == self.env.company for y in x.sale_line_ids]))
        if not to_regularize:
            raise UserError(_("No service lines to regularize"))

        invoices = self.env['account.move']
        for company in tpvs.mapped('company_id'):
            invoices |= self._create_invoices(hotels, to_regularize, company)

        if not invoices:
            raise UserError(_("No invoices created"))
        action = self.env.ref('account.action_move_in_invoice_type').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id,
                        'form')]
            if 'views' in action:
                action['views'] = form_view + \
                    [(state, view) for state, view in action['views']
                    if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.ids[0]
        return action

    def _create_invoices(self, hotels, to_regularize,invoice_company):

        invoices = self.env['account.move']
        move_type = 'in_invoice'
        journal_type = 'purchase'
        for hotel in hotels:
            partner = invoice_company.partner_id
            pricelist_to_apply = hotel.with_company(invoice_company.id).sudo().partner_id.property_product_pricelist.id
            invoice_data = self._prepare_invoice_data(hotel,partner,invoice_company,pricelist_to_apply)
            product_ids = self._group_products(to_regularize, hotel)
            invoice_vals = self._prepare_account_move_lines(product_ids, partner, invoice_company,pricelist_to_apply)
            invoice_data["invoice_line_ids"] = invoice_vals
            invoice = self.env['account.move'].create(invoice_data)
            invoices |= invoice
        return invoices

    def _prepare_account_move_lines(self, product_ids, partner, invoice_company,pricelist_to_apply):
        invoice_vals=[]
        for product_id in product_ids:
            product = self.env['product.product'].browse(product_id)
            tax_ids = partner.property_account_position_id.map_tax(
                product.supplier_taxes_id, product, partner.id)
            account_id = partner.property_account_position_id.map_account(
                product.property_account_expense_id or
                product.categ_id.
                property_account_expense_categ_id
            ).id
            price_unit = product.\
                with_company(invoice_company.id).\
                with_context(
                    pricelist=pricelist_to_apply,
                    partner=partner.id,
                    quantity=product_ids[product.id][0]).price

            invoice_line = {
                "product_id": product_id,
                "quantity": product_ids[product_id][0],
                'account_id': account_id,
                "price_unit": price_unit,
                "product_uom_id": product.uom_id.id,
                "tax_ids": [(6, 0, tax_ids.ids)],
                "service_line_ids": [(6, 0, product_ids[product_id][1])]
            }
            invoice_vals.append(invoice_line)
        return invoice_vals


    def _group_products(self, to_regularize, hotel):
        product_ids = {}
        for line in to_regularize.filtered(lambda x: x.pms_property_id == hotel):
            if line.product_id.id not in product_ids:
                product_ids[line.product_id.id] = [line.day_qty,
                                                [line.id]]
            else:
                product_ids[line.product_id.id][0] += line.day_qty
                product_ids[line.product_id.id][1].append(line.id)
        return product_ids

    def _prepare_invoice_data(self, hotel, partner, invoice_company,pricelist_to_apply):
        journal_domain = [('type', '=', 'purchase'),('pms_property_ids', 'in', [hotel.id])]
        journal = self.env['account.journal'].search(journal_domain, limit=1)
        if not journal:
            journal_domain = [('type', '=', 'purchase'),('pms_property_ids', '=', False)]
            journal = self.env['account.journal'].search(journal_domain, limit=1)
        return {
                "move_type": 'in_invoice',
                "partner_id": partner.id,
                "invoice_date": fields.Date.today(),
                "date": fields.Date.today(),
                "journal_id": journal.id,
                "currency_id": invoice_company.currency_id.id,
                "fiscal_position_id": partner.property_account_position_id.id,
                "payment_mode_id": partner.supplier_payment_mode_id.id,
                "invoice_payment_term_id":partner.property_supplier_payment_term_id.id,
            }

