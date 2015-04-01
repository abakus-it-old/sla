from openerp import models, fields, api
import datetime
from datetime import date

class account_analytic_account_sla_priority(models.Model):
    _inherit = ['account.analytic.account']
    
    #issue_priority_ids = fields.Many2many(comodel_name='project.issue.priority', relation='project_issue_priority_rel', column1='contract_id', column2='priority_id', string='Priorities')
    sla_id = fields.Many2one(comodel_name='project.sla',string="SLA",related='contract_type.sla_id', store=False)
    sla_name = fields.Char(compute='_compute_sla_name',string="SLA name", store=False)
    sla_bool = fields.Boolean(compute='_compute_sla_bool',string="SLA", store=False)

    #SLA stats
    number_successful_issue = fields.Integer(compute='_compute_number_successful_issue',string="Number of successful issue", store=False)
    number_failed_issue = fields.Integer(compute='_compute_number_failed_issue',string="Number of failed issue", store=False)
    number_closed_issue = fields.Integer(compute='_compute_number_closed_issue',string="Number of closed issue", store=False)
    percent_successful_issue = fields.Float(compute='_compute_percent_successful_issue',string="Percent of successful issue", store=False)
    #in minutes
    average_reaction_time = fields.Float(compute='_compute_average_reaction_time',string="Average reaction time", store=False)
    average_exceeded_reaction_time = fields.Float(compute='_compute_average_exceeded_reaction_time',string="Average exceeded reaction time", store=False)
    #return a chart URL
    issue_per_priority = fields.Char(compute='_compute_issue_per_priority',string="Issue per priority", store=False)
    issue_per_user = fields.Char(compute='_compute_issue_per_user',string="Issue per user", store=False)

    @api.one
    @api.onchange('contract_type')
    def _compute_sla_status(self):
        if self.contract_type and self.contract_type.sla_id:
            self.sla_status = self.contract_type.sla_id.name
        else:
            self.sla_status = ""
    
    @api.one
    @api.onchange('contract_type')
    def _compute_sla_name(self):
        if self.contract_type and self.contract_type.sla_id:
            self.sla_name = self.contract_type.sla_id.name
        else:
            self.sla_name = ""
    
    @api.one
    @api.onchange('contract_type')
    def _compute_sla_bool(self):
        if self.contract_type and self.contract_type.sla_id:
            self.sla_bool = True
        else:
            self.sla_bool = False
    
    def _get_contract_report_dates(self):
        cr = self.env.cr
        uid = self.env.user.id
        contract_report_obj = self.pool.get('contract.report')
        contract_report_id = contract_report_obj.search(cr, uid, [('id','=',1)])
        if contract_report_id:
            contract_report = contract_report_obj.browse(cr, uid, contract_report_id[0])
            if not contract_report.start_date or not contract_report.active:
                start_date = datetime.datetime.strptime("1980-01-01", "%Y-%m-%d").date().strftime("%Y-%m-%d %H:%M:%S")
            else:
                start_date = datetime.datetime.strptime(contract_report.start_date, "%Y-%m-%d").date().strftime("%Y-%m-%d %H:%M:%S")
            if not contract_report.end_date or not contract_report.active:
                end_date = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            else:
                end_date = datetime.datetime.strptime(contract_report.end_date, "%Y-%m-%d").date().strftime("%Y-%m-%d %H:%M:%S")
            return [start_date,end_date]
        else:
            return False
            
    def _dictionary_to_pie_chart_url(self, dict):
        url = "https://dev.odoo.abakus.be/report/chart/pie?"
        labels = "labels="
        sizes = "sizes="
        keys = dict.keys()
        last = len(keys)-1
        count=0
        for name in keys:
            if count == last:
                labels += str(name)
                sizes += str(dict[name])
            else:
                labels += str(name)+','
                sizes += str(dict[name])+','
            count+=1
        url = url+labels+"&"+sizes
        return url 
    
    @api.one
    def _compute_number_successful_issue(self):
        self.number_successful_issue = 0
        cr = self.env.cr
        uid = self.env.user.id
        contract_report_dates = self._get_contract_report_dates()
        if contract_report_dates:
            project_task_type_obj = self.pool.get('project.task.type')
            project_task_type_unassigned = project_task_type_obj.search(cr, uid, [('name','=','Unassigned')])
            if project_task_type_unassigned:
                project_issue_obj = self.pool.get('project.issue')
                project_issues = project_issue_obj.search(cr, uid, [('analytic_account_id', '=', self.id),('create_date','>=',contract_report_dates[0]),('create_date','<=',contract_report_dates[1]),('stage_id','!=',project_task_type_unassigned[0])])
                total = 0
                if project_issues:
                    for issue in project_issue_obj.browse(cr, uid, project_issues):
                        #Works only with reaction time
                        date_open = datetime.datetime.strptime(issue.date_open, '%Y-%m-%d %H:%M:%S')
                        create_date = datetime.datetime.strptime(issue.create_date, '%Y-%m-%d %H:%M:%S')
                        date_diff_in_minutes = (date_open - create_date).total_seconds()*60                   
                        check = False
                        for rule in issue.analytic_account_id.contract_type.sla_id.sla_rule_ids:
                            if check:
                                break
                            if date_diff_in_minutes < rule.action_time:
                                total += 1
                                check = True
                self.number_successful_issue = total

    @api.one
    def _compute_number_failed_issue(self):
        self.number_failed_issue = 0
        cr = self.env.cr
        uid = self.env.user.id
        contract_report_dates = self._get_contract_report_dates()
        if contract_report_dates:
            project_task_type_obj = self.pool.get('project.task.type')
            project_task_type_unassigned = project_task_type_obj.search(cr, uid, [('name','=','Unassigned')])
            if project_task_type_unassigned:
                project_issue_obj = self.pool.get('project.issue')
                project_issues = project_issue_obj.search(cr, uid, [('analytic_account_id', '=', self.id),('create_date','>=',contract_report_dates[0]),('create_date','<=',contract_report_dates[1]),('stage_id','!=',project_task_type_unassigned[0])])
                total = 0
                if project_issues:
                    for issue in project_issue_obj.browse(cr, uid, project_issues):
                        #Works only with reaction time
                        date_open = datetime.datetime.strptime(issue.date_open, '%Y-%m-%d %H:%M:%S')
                        create_date = datetime.datetime.strptime(issue.create_date, '%Y-%m-%d %H:%M:%S')
                        date_diff_in_minutes = (date_open - create_date).total_seconds()/60                   
                        check = False
                        for rule in issue.analytic_account_id.contract_type.sla_id.sla_rule_ids:
                            if check:
                                break
                            if date_diff_in_minutes >= rule.action_time:
                                total += 1
                                check = True
                self.number_failed_issue = total

    @api.one
    def _compute_number_closed_issue(self):
        self.number_closed_issue = 0
        cr = self.env.cr
        uid = self.env.user.id
        contract_report_dates = self._get_contract_report_dates()
        if contract_report_dates:
            project_task_type_obj = self.pool.get('project.task.type')
            project_task_type_closed = project_task_type_obj.search(cr, uid, [('name','=','Closed')])
            project_task_type_cancelled = project_task_type_obj.search(cr, uid, [('name','=','Cancelled')])
            if project_task_type_closed and project_task_type_cancelled:
                project_issue_obj = self.pool.get('project.issue')
                project_issues = project_issue_obj.search(cr, uid, [('analytic_account_id', '=', self.id),('create_date','>=',contract_report_dates[0]),('create_date','<=',contract_report_dates[1]),('stage_id','in',(project_task_type_closed[0],project_task_type_cancelled[0]))])
                if project_issues:
                    self.number_closed_issue = len(project_issues)
    
    @api.one
    def _compute_percent_successful_issue(self):
        sum = self.number_successful_issue+self.number_failed_issue
        if sum > 0:
            self.percent_successful_issue = self.number_successful_issue / sum *100
        else:
            self.percent_successful_issue = 0
    
    @api.one
    def _compute_average_reaction_time(self):
        self.average_reaction_time = 0
        cr = self.env.cr
        uid = self.env.user.id
        contract_report_dates = self._get_contract_report_dates()
        if contract_report_dates:
            project_task_type_obj = self.pool.get('project.task.type')
            project_task_type_unassigned = project_task_type_obj.search(cr, uid, [('name','=','Unassigned')])
            if project_task_type_unassigned:
                project_issue_obj = self.pool.get('project.issue')
                project_issues = project_issue_obj.search(cr, uid, [('analytic_account_id', '=', self.id),('create_date','>=',contract_report_dates[0]),('create_date','<=',contract_report_dates[1]),('stage_id','!=',project_task_type_unassigned[0])])
                average = 0
                if project_issues:
                    for issue in project_issue_obj.browse(cr, uid, project_issues):
                        date_open = datetime.datetime.strptime(issue.date_open, '%Y-%m-%d %H:%M:%S')
                        create_date = datetime.datetime.strptime(issue.create_date, '%Y-%m-%d %H:%M:%S')
                        date_diff_in_minutes = (date_open - create_date).total_seconds()/60
                        if date_diff_in_minutes>0:
                            average += date_diff_in_minutes
                    average = average / len(project_issues)
                    self.average_reaction_time = average
        
    @api.one
    def _compute_average_exceeded_reaction_time(self):
        self.average_exceeded_reaction_time = 0
        cr = self.env.cr
        uid = self.env.user.id
        contract_report_dates = self._get_contract_report_dates()
        if contract_report_dates:
            project_task_type_obj = self.pool.get('project.task.type')
            project_task_type_unassigned = project_task_type_obj.search(cr, uid, [('name','=','Unassigned')])
            if project_task_type_unassigned:
                project_issue_obj = self.pool.get('project.issue')
                project_issues = project_issue_obj.search(cr, uid, [('analytic_account_id', '=', self.id),('create_date','>=',contract_report_dates[0]),('create_date','<=',contract_report_dates[1]),('stage_id','!=',project_task_type_unassigned[0])])
                total = 0
                if project_issues:
                    for issue in project_issue_obj.browse(cr, uid, project_issues):
                        #Works only with reaction time
                        date_open = datetime.datetime.strptime(issue.date_open, '%Y-%m-%d %H:%M:%S')
                        create_date = datetime.datetime.strptime(issue.create_date, '%Y-%m-%d %H:%M:%S')
                        date_diff_in_minutes = (date_open - create_date).total_seconds()/60                   
                        check = False
                        for rule in issue.analytic_account_id.contract_type.sla_id.sla_rule_ids:
                            if check:
                                break
                            if date_diff_in_minutes >= rule.action_time:
                                total += date_diff_in_minutes
                                check = True
                    average = total / len(project_issues)     
                    self.average_exceeded_reaction_time = average

    #return a chart URL
    @api.one
    def _compute_issue_per_priority(self):
        self.issue_per_priority = ""
        cr = self.env.cr
        uid = self.env.user.id
        contract_report_dates = self._get_contract_report_dates()
        if contract_report_dates:
            project_issue_obj = self.pool.get('project.issue')
            project_issues = project_issue_obj.search(cr, uid, [('analytic_account_id', '=', self.id),('create_date','>=',contract_report_dates[0]),('create_date','<=',contract_report_dates[1])])
            total = 0
            issue_dict = {}
            priority_dict = {'0': 'Low', '1': 'Normal', '2': 'High'}
            if project_issues:
                for issue in project_issue_obj.browse(cr, uid, project_issues):
                    priority_name = priority_dict[str(issue.priority)]
                    if issue_dict.has_key(priority_name):
                        issue_dict[priority_name] += 1
                    else:
                        issue_dict[priority_name] = 1
            self.issue_per_priority = self._dictionary_to_pie_chart_url(issue_dict)
    
    #return a chart URL
    @api.one
    def _compute_issue_per_user(self):
        self.issue_per_user = ""
        cr = self.env.cr
        uid = self.env.user.id
        contract_report_dates = self._get_contract_report_dates()
        if contract_report_dates:
            project_issue_obj = self.pool.get('project.issue')
            project_issues = project_issue_obj.search(cr, uid, [('analytic_account_id', '=', self.id),('create_date','>=',contract_report_dates[0]),('create_date','<=',contract_report_dates[1])])
            total = 0
            user_dict = {}
            if project_issues:
                for issue in project_issue_obj.browse(cr, uid, project_issues):
                    if issue.user_id:
                        user_name = issue.user_id.name
                        if user_dict.has_key(user_name):
                            user_dict[user_name] += 1
                        else:
                            user_dict[user_name] = 1
            self.issue_per_user = self._dictionary_to_pie_chart_url(user_dict)
