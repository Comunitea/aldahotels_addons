from odoo import _, api, fields, models


class PmsServiceLine(models.Model):

    _inherit = "pms.service.line"

    regularize_state = fields.Selection(selection=[('regularized', 'Regularized'),
                                              ('to_regularize', 'To regularize'),
                                              ('no_regularizable', 'No regularizable')],
                                   string="Regularize state",
                                   help="Indicates if the service line is regularized or not",
                                   compute="_compute_regularized",
                                   store=True)

    invoice_line_id = fields.Many2one('account.move.line', string="Invoice line")


    @api.depends('product_id', 'invoice_line_id', 'product_id.available_in_pos', 'product_id.intercompany_regularization','pms_property_id')
    def _compute_regularized(self):
        tpvs = self.sudo().env['pos.config'].search([])
        for record in self:
            if record.invoice_line_id:
                record.regularize_state = 'regularized'
            # elif record.product_id.available_in_pos and record.product_id.intercompany_regularization:
            elif record.product_id.available_in_pos and record.product_id.intercompany_regularization and record.pms_property_id in tpvs.mapped('reservation_allowed_propertie_ids'):
                record.regularize_state = 'to_regularize'
            else:
                record.regularize_state = 'no_regularizable'
