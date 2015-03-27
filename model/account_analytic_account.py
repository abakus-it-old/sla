from openerp import models, fields, api
import datetime
from datetime import date

class account_analytic_account_sla_priority(models.Model):
    _inherit = ['account.analytic.account']
    
    #issue_priority_ids = fields.Many2many(comodel_name='project.issue.priority', relation='project_issue_priority_rel', column1='contract_id', column2='priority_id', string='Priorities')
    sla_id = fields.Many2one(comodel_name='project.sla',string="SLA",related='contract_type.sla_id', store=False)
    
    #Developing
    """
    computed_issue_successful = fields.Integer(compute='_compute_issue_successful',string="Cost price", store=False)
    computed_issue_failure = fields.Integer(compute='_compute_issue_failure',string="Cost price", store=False)

    @api.one
    def _compute_issue_successful(self):
        #If error
        self.computed_issue_successful = -1
        cr = self.env.cr
        uid = self.env.user.id
        contract_report_obj = self.pool.get('contract.report')
        contract_report_id = contract_report_obj.search(cr, uid, [('id','=',1)])
        if contract_report_id:
            contract_report = contract_report_obj.browse(cr, uid, contract_report_id[0])
            if not contract_report.start_date:
                start_date = datetime.datetime.strptime("1980-01-01", "%Y-%m-%d").date().strftime("%Y-%m-%d %H:%M:%S")
            else:
                start_date = datetime.datetime.strptime(contract_report.start_date, "%Y-%m-%d").date().strftime("%Y-%m-%d %H:%M:%S")
            if not contract_report.end_date:
                end_date = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            else:
                end_date = datetime.datetime.strptime(contract_report.end_date, "%Y-%m-%d").date().strftime("%Y-%m-%d %H:%M:%S")
            project_issue_obj = self.pool.get('project.issue')
            project_issues = project_issue_obj.search(cr, uid, [('analytic_account_id', '=', self.id),('create_date','>=',start_date),('date_closed','<=',end_date)])
            if project_issues:
                total = 0
                for issue in obj.browse(cr, uid, project_issues):
                    #Works only with reaction time
                    date_open = datetime.datetime.strptime(issue.date_open, '%Y-%m-%d %H:%M:%S')
                    create_date = datetime.datetime.strptime(issue.create_date, '%Y-%m-%d %H:%M:%S')
                    date_diff_in_minutes = (date_open - create_date).total_seconds()*60                   
                    for rule in issue.project_id.analytic_account_id.contract_type.sla_id.sla_rule_ids:
                        if date_diff_in_minutes < rule.action_time:
                            total += 1
            self.computed_issue_successful = total

    @api.one
    def _compute_issue_failure(self):
        #If error
        self.computed_issue_successful = -1
        cr = self.env.cr
        uid = self.env.user.id
        contract_report_obj = self.pool.get('contract.report')
        contract_report_id = contract_report_obj.search(cr, uid, [('id','=',1)])
        if contract_report_id:
            contract_report = contract_report_obj.browse(cr, uid, contract_report_id[0])
            if not contract_report.start_date:
                start_date = datetime.datetime.strptime("1980-01-01", "%Y-%m-%d").date().strftime("%Y-%m-%d %H:%M:%S")
            else:
                start_date = datetime.datetime.strptime(contract_report.start_date, "%Y-%m-%d").date().strftime("%Y-%m-%d %H:%M:%S")
            if not contract_report.end_date:
                end_date = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            else:
                end_date = datetime.datetime.strptime(contract_report.end_date, "%Y-%m-%d").date().strftime("%Y-%m-%d %H:%M:%S")
            project_issue_obj = self.pool.get('project.issue')
            project_issues = project_issue_obj.search(cr, uid, [('analytic_account_id', '=', self.id),('create_date','>=',start_date),('date_closed','<=',end_date)])
            if project_issues:
                total = 0
                for issue in obj.browse(cr, uid, project_issues):
                    #Works only with reaction time
                    date_open = datetime.datetime.strptime(issue.date_open, '%Y-%m-%d %H:%M:%S')
                    create_date = datetime.datetime.strptime(issue.create_date, '%Y-%m-%d %H:%M:%S')
                    date_diff_in_minutes = (date_open - create_date).total_seconds()*60                   
                    for rule in issue.project_id.analytic_account_id.contract_type.sla_id.sla_rule_ids:
                        if date_diff_in_minutes >= rule.action_time:
                            total += 1
            self.computed_issue_successful = total
    """