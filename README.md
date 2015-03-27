This modules adds the SLA management for AbAKUS.

    - It adds in contract type a SLA field.
    - You can select many rules in SLA.
    - For one rule, you can select many action. This actions are Python code that saved in database.
    - It adds one cron that is active every 5 minutes. It checks if a issue from a contract is over the action time from the SLA rule.
    - The cron also checks the time difference between the create date and now with the working hours.
    - The working hour needs to be called "SLA". Two times the same day in working hour is not allowed.
    
This module has been developed by Bernard Delhez, intern @ AbAKUS it-solutions, under the control of Valentin Thirion.""",