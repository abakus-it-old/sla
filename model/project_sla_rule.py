from openerp import models, fields, api

class project_sla_rule(models.Model):
    _name = 'project.sla.rule'

    def _get_priorities(self):
        return [('0', 'Low'),
                ('1', 'Normal'),
                ('2', 'High')
               ]
    def _get_stages(self):
        return [('Unassigned', 'Unassigned'),
                ('Open', 'Open'),
                ('Pending Supplier feedback', 'Pending Supplier feedback'),
                ('Pending Customer feedback', 'Pending Customer feedback'),
                #('Closed', 'Closed'),
                #('Cancelled', 'Cancelled')
               ]
    
    name = fields.Char(string="Name")
    issue_priority = fields.Selection(selection='_get_priorities')
    issue_stage = fields.Selection(selection='_get_stages')
    service_type = fields.Selection([('os', 'On Site'), ('sd', 'Service Desk')], string='Service type')
    time_type = fields.Selection([('reaction', 'Reaction'), ('resolution', 'Resolution')], string='Time type')
    action_time = fields.Integer(string="Action Time in minutes")
    sla_action = fields.Many2many(comodel_name='project.sla.action', string="SLA action")
    sla_id = fields.Many2one(comodel_name='project.sla', string="SLA")