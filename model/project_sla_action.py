from openerp import models, fields, api

class project_sla_action(models.Model):
    _name = 'project.sla.action'

    name = fields.Char(string="Name")
    action = fields.Text(string="Action")