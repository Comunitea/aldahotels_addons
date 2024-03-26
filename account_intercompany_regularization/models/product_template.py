from odoo import _, api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    intercompany_regularization = fields.Boolean(
        string="Intercompany Regularization",
        help="Indicates if the product is used in intercompany regularization",
        default=False,)
