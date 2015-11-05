from openerp import models, fields, api
import datetime
from datetime import date
from pytz import timezone

class project_issue_sla(models.Model):
    _inherit = ['project.issue']

    #priority_sla = fields.Many2one(comodel_name='project.issue.priority', string="Issue's priority")
    sla_rule_ids = fields.One2many(comodel_name='project.sla.rule',inverse_name='sla_id', related='analytic_account_id.contract_type.sla_id.sla_rule_ids', string="SLA rules", store=False)
    sla_bool = fields.Boolean(related='analytic_account_id.sla_bool', string="SLA", store=False)
    
    def get_date_difference_with_working_time_in_minutes(self, cr, uid, create_date, check_date):
        resource_calendar_obj = self.pool.get('resource.calendar')
        resource_calendars = resource_calendar_obj.search(cr, uid, [('name','ilike','sla')])
        if resource_calendars:
            resource_calendar_attendance_obj = self.pool.get('resource.calendar.attendance')
            time_diff = 0
            now_date = check_date + datetime.timedelta(seconds=0)
            cursor_date = create_date + datetime.timedelta(seconds=0)
            now_hour_float = float(check_date.strftime('%H')+'.'+str(int(float('0.'+check_date.strftime('%M'))/60*10000)))
            create_hour_float = float(create_date.strftime('%H')+'.'+str(int(float('0.'+create_date.strftime('%M'))/60*10000)))
            dayofweek_dict = {'0': '6', '1': '0', '2': '1', '3': '2', '4': '3', '5': '4', '6': '5'}
            count = 0
            while True:
                #return Weekday as a decimal number, where 0 is Sunday and 6 is Saturday.
                cursor_dayofweek = cursor_date.strftime("%w")
                #dayofweek selection: Monday 0, Tuesday 1, Wednesday 2, Thursday 3, Friday 4, Saturday 5, Sunday 6
                resource_calendar_attendance = resource_calendar_attendance_obj.search(cr, uid, [('calendar_id','=',resource_calendars[0]),('dayofweek','=',dayofweek_dict[str(cursor_dayofweek)])])
                if not resource_calendar_attendance:
                    if cursor_date.date() < now_date.date():
                        cursor_date += datetime.timedelta(days=1)
                        continue
                    else:
                        break
                else:
                    working_hour_dayofweek = resource_calendar_attendance_obj.browse(cr, uid, resource_calendar_attendance[0])
                    hour_from = working_hour_dayofweek.hour_from
                    hour_to = working_hour_dayofweek.hour_to
                
                if create_date.strftime('%d%m%Y') == now_date.strftime('%d%m%Y'):
                    if hour_from <= create_hour_float <= hour_to and hour_from <= now_hour_float <= hour_to:
                        time_diff += now_hour_float - create_hour_float
                    elif create_hour_float < hour_from and now_hour_float > hour_from:
                        if now_hour_float > hour_to:
                            time_diff += hour_to - hour_from
                        elif now_hour_float <= hour_to:
                            time_diff += now_hour_float - hour_from                    
                    break
                elif cursor_date.strftime('%d%m%Y') == now_date.strftime('%d%m%Y'):  
                    if now_hour_float > hour_to:
                        time_diff += hour_to - hour_from
                    else:
                        time_diff += now_hour_float - hour_from
                    break
                elif count == 0: 
                    if hour_from <= create_hour_float <= hour_to:
                        time_diff += hour_to - create_hour_float
                    elif create_hour_float < hour_from:
                        time_diff += hour_to - hour_from
                else:
                    time_diff += hour_to - hour_from
                
                cursor_date += datetime.timedelta(days=1)
                if count > 30:
                    break
                count += 1
            return time_diff*60
        return 0
    
    def check_date_in_working_time(self, cr, uid, check_date):
        resource_calendar_obj = self.pool.get('resource.calendar')
        resource_calendars = resource_calendar_obj.search(cr, uid, [('name','ilike','sla')])
        if resource_calendars:
            resource_calendar_attendance_obj = self.pool.get('resource.calendar.attendance')
            dayofweek_dict = {'0': '6', '1': '0', '2': '1', '3': '2', '4': '3', '5': '4', '6': '5'}
            #return Weekday as a decimal number, where 0 is Sunday and 6 is Saturday.
            cursor_dayofweek = check_date.strftime("%w")
            #dayofweek selection: Monday 0, Tuesday 1, Wednesday 2, Thursday 3, Friday 4, Saturday 5, Sunday 6
            resource_calendar_attendance = resource_calendar_attendance_obj.search(cr, uid, [('calendar_id','=',resource_calendars[0]),('dayofweek','=',dayofweek_dict[str(cursor_dayofweek)])])
            if not resource_calendar_attendance:
                return False
            else:
                working_hour_dayofweek = resource_calendar_attendance_obj.browse(cr, uid, resource_calendar_attendance[0])
                hour_from = working_hour_dayofweek.hour_from
                hour_to = working_hour_dayofweek.hour_to
                check_date_hour_float = float(check_date.strftime('%H')+'.'+str(int(float('0.'+check_date.strftime('%M'))/60*10000)))
                return hour_from <= check_date_hour_float <= hour_to
 
        return False

        
        
    #dates needs to be in timezone('Europe/Brussels')
    def is_issue_SLA_compliant(self, cr, uid, issue_id , start_date, end_date):
        issue_ids = self.pool.get('project.issue').search(cr, uid, [('id','=',issue_id)])
        if issue_ids:
            issue = self.pool.get('project.issue').browse(cr, uid, issue_ids[0])
            #check if SLA exists on contract.
            if issue.project_id and issue.project_id.analytic_account_id and issue.project_id.analytic_account_id.contract_type and issue.project_id.analytic_account_id.contract_type.sla_id:
                #loop SLA rules
                for rule in issue.project_id.analytic_account_id.contract_type.sla_id.sla_rule_ids:
                    #check the issue's priority and issue's stage
                    if rule.issue_priority == issue.priority:
                        service_type = 'sd'
                        for timesheet in issue.timesheet_ids:
                            if timesheet.on_site:
                                service_type = 'os'
                                break
                        if rule.service_type == service_type:
                            difference_in_minutes = self.get_date_difference_with_working_time_in_minutes(cr, uid, start_date, end_date)
                            if difference_in_minutes <= rule.action_time:
                                return True
        return False

    def execute_rule_if_issue_is_SLA_non_compliant(self, cr, uid, issue_id , start_date, end_date):
        issue_ids = self.pool.get('project.issue').search(cr, uid, [('id','=',issue_id)])
        if issue_ids:
            issue = self.pool.get('project.issue').browse(cr, uid, issue_ids[0])
            #check if SLA exists on contract.
            if issue.project_id and issue.project_id.analytic_account_id and issue.project_id.analytic_account_id.contract_type and issue.project_id.analytic_account_id.contract_type.sla_id:
                #loop SLA rules
                for rule in issue.project_id.analytic_account_id.contract_type.sla_id.sla_rule_ids:
                    #check the issue's priority and issue's stage
                    if rule.issue_priority == issue.priority:
                        service_type = 'sd'
                        for timesheet in issue.timesheet_ids:
                            if timesheet.on_site:
                                service_type = 'os'
                                break
                        if rule.service_type == service_type:
                            difference_in_minutes = self.get_date_difference_with_working_time_in_minutes(cr, uid, start_date, end_date)
                            if difference_in_minutes >= rule.action_time:
                                for action in rule.sla_action:
                                    try:
                                        exec(action.action.replace(r'\n','\n'))
                                    except:
                                        pass
    
    
    def _cron_project_sla(self, cr, uid, context=None):
        if self.check_date_in_working_time(cr, uid, datetime.datetime.now(timezone('Europe/Brussels'))):
            project_sla_rule_obj = self.pool.get('project.sla.rule')
            project_sla_rules = project_sla_rule_obj.search(cr, uid, [])
            if project_sla_rules:
                stages_dic = {}
                #create a dictionary with the used stages from SLA rules
                for rule_stage in project_sla_rule_obj.browse(cr, uid, project_sla_rules):
                    if not stages_dic.has_key(rule_stage.issue_stage):
                        stages_dic[rule_stage.issue_stage]=1
                for stage in stages_dic.keys():
                    project_task_type_obj = self.pool.get('project.task.type')
                    project_task_type = project_task_type_obj.search(cr, uid, [('name','=',stage)])
                    if project_task_type:
                        project_issue_obj = self.pool.get('project.issue')
                        project_issue_ids = project_issue_obj.search(cr, uid, [('stage_id','=',project_task_type[0])])
                        if project_issue_ids:
                            #loop all issues with the SLA rule stage
                            for issue in project_issue_obj.browse(cr, uid, project_issue_ids):
                                #check the minutes between the issue's creation date with now.
                                local_tz = timezone('Europe/Brussels')
                                now = datetime.datetime.now(local_tz)
                                date = datetime.datetime.strptime(issue.create_date, '%Y-%m-%d %H:%M:%S')
                                create_date = local_tz.localize(date, is_dst=None)
                                self.execute_rule_if_issue_is_SLA_non_compliant(cr,uid,issue.id,create_date,now)                                   