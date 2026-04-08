from odoo import models, fields, api, _
from datetime import date

class ChurchAttendanceType(models.Model):
    _name = 'church.attendance.type'
    _description = 'Attendance session type'
    
    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True, help="Example: ASSEMBLY")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

class ChurchAttendance(models.Model):
    _name = 'church.attendance'
    _description = 'Attendance session'
    _order = 'date desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reference', compute='_compute_name', store=True)
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True, tracking=True)
    attendance_type_id = fields.Many2one('church.attendance.type', string='Attendance type', required=True, tracking=True)
    criteria = fields.Selection([
        ('all', 'All members'),
        ('active', 'Active members'),
        ('baptized', 'Baptized members'),
        ('not_baptized', 'Non-baptized members'),
        ('assembly', 'Assembly members')
    ], string='Criteria', default='active', required=True, tracking=True)
    responsible_id = fields.Many2one('res.partner', string='Responsible', tracking=True)
    
    state = fields.Selection([
        ('pendiente', 'Draft'),
        ('abierto', 'Open'),
        ('cerrado', 'Closed')
    ], string='Status', default='pendiente', tracking=True)

    line_ids = fields.One2many('church.attendance.line', 'attendance_id', string='Attendance lines')

    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    # Indicators
    total_members = fields.Integer(string='Total members', compute='_compute_counts', store=True)
    total_attendance = fields.Integer(string='Attendance', compute='_compute_counts', store=True)
    total_absence = fields.Integer(string='Absence', compute='_compute_counts', store=True)
    total_excuse = fields.Integer(string='Excuse', compute='_compute_counts', store=True)

    # Quorum
    x_requires_quorum = fields.Boolean(string='Requires quorum', default=False, tracking=True)
    x_quorum_needed = fields.Integer(string='Quorum needed', compute='_compute_counts', store=True)
    x_has_quorum = fields.Boolean(string='Has quorum?', compute='_compute_counts', store=True)

    @api.depends('attendance_type_id', 'date')
    def _compute_name(self):
        for record in self:
            if record.attendance_type_id and record.date:
                record.name = f"{record.attendance_type_id.code}-{record.date}"
            else:
                record.name = _("New attendance session")

    @api.depends('line_ids.status', 'x_requires_quorum')
    def _compute_counts(self):
        for record in self:
            lines = record.line_ids
            record.total_members = len(lines)
            record.total_attendance = len(lines.filtered(lambda l: l.status == 'si'))
            record.total_absence = len(lines.filtered(lambda l: l.status == 'no'))
            record.total_excuse = len(lines.filtered(lambda l: l.status == 'excusa'))
            
            # Quorum Calculation: (Active Members / 2) + 1
            # Since lines only load active members, we use total_members.
            record.x_quorum_needed = (record.total_members // 2) + 1
            record.x_has_quorum = record.total_attendance >= record.x_quorum_needed

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if not record.line_ids:
                record._load_members()
        return records

    def _get_member_domain(self):
        self.ensure_one()
        # Base domain: only church members, filtered by company
        domain = [
            ('x_is_church_member', '=', True),
            '|',
            ('company_id', '=', False),
            ('company_id', '=', self.company_id.id),
        ]
        
        # Apply criteria
        if self.criteria == 'active':
            domain.append(('active', '=', True))
        elif self.criteria == 'baptized':
            domain.extend([('active', '=', True), ('x_baptized', '=', True)])
        elif self.criteria == 'not_baptized':
            domain.extend([('active', '=', True), ('x_baptized', '=', False)])
        elif self.criteria == 'assembly':
            domain.extend([('active', '=', True), ('x_applies_for_assembly', '=', True)])
        # 'all' implies no additional active filtering or baptized filtering, just all church members
        return domain

    def _sync_attendance_lines(self):
        for record in self:
            if record.state == 'cerrado':
                continue
            
            target_domain = record._get_member_domain()
            target_members = self.env['res.partner'].search(target_domain)
            target_member_ids = set(target_members.ids)
            
            current_lines = record.line_ids
            partner_ids_in_lines = set()
            for line in current_lines:
                # We need the real database ID for comparison
                p_id = line.partner_id._origin.id if hasattr(line.partner_id, '_origin') and line.partner_id._origin else line.partner_id.id
                if p_id:
                    partner_ids_in_lines.add(p_id)

            # 1. Add missing members
            missing_member_ids = target_member_ids - partner_ids_in_lines
            new_lines_commands = []
            
            if missing_member_ids:
                # Search again to get them in order
                new_members = self.env['res.partner'].search([('id', 'in', list(missing_member_ids))], order='name asc')
                for member in new_members:
                    new_lines_commands.append((0, 0, {
                        'partner_id': member.id,
                        'status': 'no',
                    }))
            
            # 2. Identify lines to remove
            # Must be: (Not in target AND status is 'no') 
            # OR (Not active/church member AND status is 'no')
            lines_to_remove = current_lines.filtered(
                lambda l: (
                    (l.partner_id.id not in target_member_ids) or
                    (not l.partner_id.active) or
                    (not l.partner_id.x_is_church_member)
                ) and l.status == 'no'
            )
            
            for line in lines_to_remove:
                # Use (2, ID) to delete the line
                # If it's a new record in onchange, we use (2, line.id)
                new_lines_commands.append((2, line.id))
            
            if new_lines_commands:
                record.update({'line_ids': new_lines_commands})

    def _load_members(self):
        self._sync_attendance_lines()

    @api.onchange('criteria')
    def _onchange_criteria(self):
        self._sync_attendance_lines()

    def action_open(self):
        self.write({'state': 'abierto'})

    def action_close(self):
        self.write({'state': 'cerrado'})

    def action_draft(self):
        self.write({'state': 'pendiente'})

    def action_refresh_members(self):
        self.ensure_one()
        self._sync_attendance_lines()
        return True

class ChurchAttendanceLine(models.Model):
    _name = 'church.attendance.line'
    _description = 'Attendance line'
    _order = 'partner_name asc'

    attendance_id = fields.Many2one('church.attendance', string='Attendance session', ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Member', required=True)
    partner_name = fields.Char(related='partner_id.name', store=True) # For sorting
    
    status = fields.Selection([
        ('si', 'Yes'),
        ('no', 'No'),
        ('excusa', 'Excuse')
    ], string='Attendance', default='no')
    
    excuse_reason = fields.Text(string='Excuse reason')
    company_id = fields.Many2one(
        'res.company', string='Company',
        related='attendance_id.company_id', store=True,
    )
