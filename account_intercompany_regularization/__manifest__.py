{
    "name": "Intercompany accounting regularization",
    "version": "14.0.1.0.0",
    "category": "Accounting",
    "description": """Wizard to regularice with invoices intercompany""",
    "author": "Comunitea",
    "website": "https://www.comunitea.com",
    "depends": [
        "product_tax_multicompany_default",
        "purchase",
        "sale",
        "account_invoice_inter_company",
        "pms",
        "pos_pms_link",
    ],
    "data": [
        'security/ir.model.access.csv',
        'wizard/wzd_intercompany_invoice.xml',
        'views/product_views.xml',
        'views/pms_views.xml'
    ],
    "installable": True,
}
