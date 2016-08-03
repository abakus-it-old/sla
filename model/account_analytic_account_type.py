from openerp import models, fields, api

class account_analytic_account_type_sla(models.Model):
    _inherit = ['account.analytic.account.type']

    sla_id = fields.Many2one(comodel_name='project.sla', string="SLA")