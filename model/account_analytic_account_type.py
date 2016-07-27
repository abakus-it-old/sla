from openerp import models, fields, api

class account_analytic_account_type_sla(models.Model):
    _inherit = ['sale.subscription.type']

    sla_id = fields.Many2one(comodel_name='project.sla', string="SLA")