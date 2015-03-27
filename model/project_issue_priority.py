"""
from openerp import models, fields, api

class project_issue_priority(models.Model):
    _name = 'project.issue.priority'
    _order = 'sequence'

    name = fields.Char(string='Name')
    sequence = fields.Integer(string='Sequence', default=1)
    contract_ids = fields.Many2many(comodel_name='account.analytic.account', relation='project_issue_priority_rel', column1='priority_id', column2='contract_id', string='Contracts')
"""