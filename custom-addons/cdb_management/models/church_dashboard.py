from odoo import models, fields, api
from datetime import date, timedelta

class ChurchDashboard(models.TransientModel):
    _name = 'church.dashboard'
    _description = 'Church dashboard'

    name = fields.Char(default="Dashboard")
    
    member_count = fields.Integer(string='Total members', compute='_compute_stats')
    avg_attendance = fields.Float(string='Total Average', compute='_compute_stats')
    avg_presencial = fields.Float(string='Presencial Average', compute='_compute_stats')
    avg_online = fields.Float(string='Online Average', compute='_compute_stats')
    baptized_count = fields.Integer(string='Baptized members', compute='_compute_stats')
    non_baptized_count = fields.Integer(string='Non-baptized members', compute='_compute_stats')
    
    active_tab = fields.Selection([
        ('today', 'Today'),
        ('week', 'This Week'),
        ('next_week', 'Next Week'),
        ('month', 'This Month'),
        ('year', 'This Year')
    ], default='month', string='Active Tab')
    
    # Birthday Lists
    birthday_today_ids = fields.Many2many('res.partner', string='Birthdays today', compute='_compute_birthdays')
    birthday_week_ids = fields.Many2many('res.partner', string='Birthdays this week', compute='_compute_birthdays')
    birthday_next_week_ids = fields.Many2many('res.partner', string='Birthdays next week', compute='_compute_birthdays')
    birthday_month_ids = fields.Many2many('res.partner', string='Birthdays this month', compute='_compute_birthdays')
    birthday_year_ids = fields.Many2many('res.partner', string='Birthdays this year', compute='_compute_birthdays')
    
    # Yearly Activities
    yearly_activity_ids = fields.Many2many('church.activity', string='Yearly Activities', compute='_compute_yearly_activities')

    def _get_company_domain(self):
        """Return a base domain fragment to filter by current company."""
        return [
            '|',
            ('company_id', '=', False),
            ('company_id', 'in', self.env.companies.ids),
        ]

    def _compute_stats(self):
        Partner = self.env['res.partner']
        AttendanceReport = self.env['church.attendance.report']
        
        company_domain = self._get_company_domain()
        
        member_count = Partner.search_count(
            company_domain + [('x_is_church_member', '=', True), ('active', '=', True)]
        )
        baptized_count = Partner.search_count(
            company_domain + [('x_is_church_member', '=', True), ('active', '=', True), ('x_baptized', '=', True)]
        )
        non_baptized_count = member_count - baptized_count
        
        # Reports filtered by company
        reports = AttendanceReport.search(company_domain)
        if reports:
            avg_attendance = sum(reports.mapped('total_attendance')) / len(reports)
            avg_presencial = sum(reports.mapped('presencial_count')) / len(reports)
            avg_online = sum(reports.mapped('online_count')) / len(reports)
        else:
            avg_attendance = 0.0
            avg_presencial = 0.0
            avg_online = 0.0
            
        for record in self:
            record.member_count = member_count
            record.avg_attendance = avg_attendance
            record.avg_presencial = avg_presencial
            record.avg_online = avg_online
            record.baptized_count = baptized_count
            record.non_baptized_count = non_baptized_count

    def _compute_yearly_activities(self):
        today = date.today()
        company_domain = self._get_company_domain()
        # Find activities for this current year
        activities = self.env['church.activity'].search(
            company_domain + [
                ('date', '>=', f'{today.year}-01-01'),
                ('date', '<=', f'{today.year}-12-31')
            ], order='date asc')
        for record in self:
            record.yearly_activity_ids = [(6, 0, activities.ids)]

    def _compute_birthdays(self):
        today = date.today()
        # Week calculations
        start_week = today - timedelta(days=today.weekday())
        end_week = start_week + timedelta(days=6)
        
        start_next_week = start_week + timedelta(days=7)
        end_next_week = start_next_week + timedelta(days=6)

        company_domain = self._get_company_domain()

        # We search for members filtered by company
        members = self.env['res.partner'].search(
            company_domain + [
                ('x_is_church_member', '=', True),
                ('active', '=', True),
                ('x_birthdate', '!=', False)
            ]
        )

        for record in self:
            today_list = []
            week_list = []
            next_week_list = []
            month_list = []
            year_list = []

            for member in members:
                b = member.x_birthdate
                # Create a date for this year
                try:
                    b_date = date(today.year, b.month, b.day)
                except ValueError: # Leap year case (Feb 29)
                    b_date = date(today.year, 3, 1)

                if b_date == today:
                    today_list.append(member.id)
                
                if start_week <= b_date <= end_week:
                    week_list.append(member.id)
                
                if start_next_week <= b_date <= end_next_week:
                    next_week_list.append(member.id)
                
                if b.month == today.month:
                    month_list.append(member.id)
                
                # "By Year" represents all birthdays in the system for this context
                year_list.append(member.id)

            record.birthday_today_ids = [(6, 0, today_list)]
            record.birthday_week_ids = [(6, 0, week_list)]
            record.birthday_next_week_ids = [(6, 0, next_week_list)]
            record.birthday_month_ids = [(6, 0, month_list)]
            record.birthday_year_ids = [(6, 0, year_list)]

    def _compute_display_name(self):
        for record in self:
            record.display_name = "Dashboard"

    name = fields.Char(default="Dashboard") # Keep for internal reference if needed

    @api.model
    def action_open_dashboard(self):
        # Create a transient record
        dashboard = self.create({})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Dashboard',
            'res_model': 'church.dashboard',
            'res_id': dashboard.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_refresh(self):
        """Action for the refresh button."""
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_set_tab(self):
        """Action to switch tabs in the dashboard."""
        self.ensure_one()
        tab = self.env.context.get('tab')
        if tab:
            self.active_tab = tab
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'church.dashboard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }
