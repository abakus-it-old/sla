# -*- coding: utf-8 -*-

from openerp import models, fields, api
from datetime import date, datetime, timedelta
from pytz import timezone

class project_issue_sla(models.Model):
    _inherit = 'project.issue'

    sla_rule_ids = fields.One2many(comodel_name='project.sla.rule',inverse_name='sla_id', related='project_id.sale_subscription_id.contract_type.sla_id.sla_rule_ids', string="SLA rules", store=False)
    sla_bool = fields.Boolean(related='project_id.sale_subscription_id.sla_bool', string="SLA", store=False)
    sla_compliant = fields.Boolean(compute="_is_SLA_compliant", string="SLA compliant")
    
    @api.model
    def get_date_difference_with_working_time_in_minutes(self, create_date, check_date):
        resource_calendars = self.env['resource.calendar'].search([('name','ilike','sla')])
        if resource_calendars:
            time_diff = 0
            now_date = check_date + timedelta(seconds=0)
            cursor_date = create_date + timedelta(seconds=0)
            now_hour_float = float(check_date.strftime('%H')+'.'+str(int(float('0.'+check_date.strftime('%M'))/60*10000)))
            create_hour_float = float(create_date.strftime('%H')+'.'+str(int(float('0.'+create_date.strftime('%M'))/60*10000)))
            dayofweek_dict = {'0': '6', '1': '0', '2': '1', '3': '2', '4': '3', '5': '4', '6': '5'}
            count = 0
            while True:
                #return Weekday as a decimal number, where 0 is Sunday and 6 is Saturday.
                cursor_dayofweek = cursor_date.strftime("%w")
                #dayofweek selection: Monday 0, Tuesday 1, Wednesday 2, Thursday 3, Friday 4, Saturday 5, Sunday 6
                resource_calendar_attendance = self.env['resource.calendar.attendance'].search([('calendar_id','=',resource_calendars[0]),('dayofweek','=',dayofweek_dict[str(cursor_dayofweek)])])
                if not resource_calendar_attendance:
                    if cursor_date.date() < now_date.date():
                        cursor_date += timedelta(days=1)
                        continue
                    else:
                        break
                else:
                    working_hour_dayofweek = self.env['resource.calendar.attendance'].browse(resource_calendar_attendance[0])
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
                
                cursor_date += timedelta(days=1)
                if count > 30:
                    break
                count += 1
            return time_diff*60
        return 0
    
    @api.model
    def check_date_in_working_time(self, check_date):
        resource_calendars = self.env['resource.calendar'].search([('name','ilike','sla')], limit=1)
        if resource_calendars:
            dayofweek_dict = {'0': '6', '1': '0', '2': '1', '3': '2', '4': '3', '5': '4', '6': '5'}
            #return Weekday as a decimal number, where 0 is Sunday and 6 is Saturday.
            cursor_dayofweek = check_date.strftime("%w")
            #dayofweek selection: Monday 0, Tuesday 1, Wednesday 2, Thursday 3, Friday 4, Saturday 5, Sunday 6
            resource_calendar_attendance = self.env['resource.calendar.attendance'].search([('calendar_id','=',resource_calendars.id),('dayofweek','=',dayofweek_dict[str(cursor_dayofweek)])], limit=1)
            if not resource_calendar_attendance:
                return False
            else:
                hour_from = resource_calendar_attendance.hour_from
                hour_to = resource_calendar_attendance.hour_to
                check_date_hour_float = float(check_date.strftime('%H')+'.'+str(int(float('0.'+check_date.strftime('%M'))/60*10000)))
                return hour_from <= check_date_hour_float <= hour_to
 
        return False

    @api.one
    def _is_SLA_compliant(self):
        if self.date_open == False:
            return False

        local_tz = timezone('Europe/Brussels')
        date_open = local_tz.localize(datetime.strptime(self.date_open, '%Y-%m-%d %H:%M:%S'))
        create_date = local_tz.localize(datetime.strptime(self.create_date, '%Y-%m-%d %H:%M:%S'))
        return self.env['project.issue'].is_issue_SLA_compliant(self.id, create_date, date_open)
        
        
    #dates needs to be in timezone('Europe/Brussels')
    @api.model
    def is_issue_SLA_compliant(self, issue_id , start_date, end_date):
        issue = self.browse(issue_id)
        if issue:
            #check if SLA exists on contract.
            if issue.project_id and issue.project_id.sale_subscription_id and issue.project_id.sale_subscription_id.contract_type and issue.project_id.sale_subscription_id.contract_type.sla_id:
                #loop SLA rules
                for rule in issue.project_id.sale_subscription_id.contract_type.sla_id.sla_rule_ids:
                    #check the issue's priority and issue's stage
                    if rule.issue_priority == issue.priority:
                        service_type = 'sd'
                        for timesheet in issue.timesheet_ids:
                            if timesheet.on_site:
                                service_type = 'os'
                                break
                        if rule.service_type == service_type:
                            difference_in_minutes = self.get_date_difference_with_working_time_in_minutes(start_date, end_date)
                            if difference_in_minutes <= rule.action_time:
                                return True
        return False

    @api.model
    def execute_rule_if_issue_is_SLA_non_compliant(self, issue_id , start_date, end_date):
        issue = self.browse(issue_id)
        if issue:
            #check if SLA exists on contract.
            if issue.project_id and issue.project_id.sale_subscription_id and issue.project_id.sale_subscription_id.contract_type and issue.project_id.sale_subscription_id.contract_type.sla_id:
                #loop SLA rules
                for rule in issue.project_id.sale_subscription_id.contract_type.sla_id.sla_rule_ids:
                    #check the issue's priority and issue's stage
                    if rule.issue_priority == issue.priority:
                        service_type = 'sd'
                        for timesheet in issue.timesheet_ids:
                            if timesheet.on_site:
                                service_type = 'os'
                                break
                        if rule.service_type == service_type:
                            difference_in_minutes = self.get_date_difference_with_working_time_in_minutes(start_date, end_date)
                            if difference_in_minutes >= rule.action_time:
                                for action in rule.sla_action:
                                    try:
                                        exec(action.action.replace(r'\n','\n'))
                                    except:
                                        pass
    
    @api.model
    def _cron_project_sla(self):
        if self.check_date_in_working_time(datetime.now(timezone('Europe/Brussels'))):
            project_sla_rules = self.env['project.sla.rule'].search([])
            if project_sla_rules:
                stages_dic = {}
                #create a dictionary with the used stages from SLA rules
                for rule_stage in project_sla_rules:
                    if not stages_dic.has_key(rule_stage.issue_stage):
                        stages_dic[rule_stage.issue_stage]=1
                for stage in stages_dic.keys():
                    project_task_type = self.env['project.task.type'].search([('name','=',stage)], limit=1)
                    if project_task_type:
                        project_issues = self.env['project.issue'].search([('stage_id','=',project_task_type.id)])
                        if project_issues:
                            #loop all issues with the SLA rule stage
                            for issue in project_issues:
                                #check the minutes between the issue's creation date with now.
                                local_tz = timezone('Europe/Brussels')
                                now = datetime.now(local_tz)
                                date = datetime.strptime(issue.create_date, '%Y-%m-%d %H:%M:%S')
                                create_date = local_tz.localize(date, is_dst=None)
                                self.execute_rule_if_issue_is_SLA_non_compliant(issue.id, create_date, now)                                   