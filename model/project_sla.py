from openerp import models, fields, api

class project_sla(models.Model):
    _name = 'project.sla'

    name = fields.Char(string="Name")
    description = fields.Text(string="Description")
    sla_rule_ids = fields.One2many(comodel_name='project.sla.rule', inverse_name='sla_id', string="SLA rule")