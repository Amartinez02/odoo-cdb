from odoo import models, fields, api

class ChurchAttendanceReport(models.Model):
    _name = 'church.attendance.report'
    _description = 'Attendance report'
    _order = 'date desc, id desc'

    name = fields.Char(string='Reference', compute='_compute_name', store=True)
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True)
    presencial_count = fields.Integer(string='Presencial Attendance', default=0)
    online_count = fields.Integer(string='Online Attendance', default=0)
    total_attendance = fields.Integer(string='Total Attendance', compute='_compute_total_attendance', store=True)
    new_attendee_line_ids = fields.One2many('church.attendance.report.new.line', 'report_id', string='New visitors')
    notes = fields.Text(string='Notes')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    @api.depends('presencial_count', 'online_count')
    def _compute_total_attendance(self):
        for record in self:
            record.total_attendance = record.presencial_count + record.online_count

    @api.depends('date')
    def _compute_name(self):
        for record in self:
            if record.date:
                record.name = f"Report - {record.date}"
            else:
                record.name = "New report"

class ChurchAttendanceReportNewLine(models.Model):
    _name = 'church.attendance.report.new.line'
    _description = 'New attendee line'

    report_id = fields.Many2one('church.attendance.report', string='Report', ondelete='cascade')
    name = fields.Char(string='Name', required=True)
    invited_by_id = fields.Many2one('res.partner', string='Invited by', domain=[('x_is_church_member', '=', True)])
    visit_reason = fields.Char(string='Visit Reason')
    company_id = fields.Many2one(
        'res.company', string='Company',
        related='report_id.company_id', store=True,
    )
