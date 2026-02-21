from odoo import models, fields, api, _
from datetime import date

class ChurchAttendanceType(models.Model):
    _name = 'church.attendance.type'
    _description = 'Attendance session type'
    
    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True, help="Example: ASSEMBLY")
    active = fields.Boolean(default=True)

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

    def _load_members(self):
        for record in self:
            if record.state != 'pendiente':
                continue

            # Base domain: only church members
            domain = [('x_is_church_member', '=', True)]
            
            # Apply criteria
            if record.criteria == 'active':
                domain.append(('active', '=', True))
            elif record.criteria == 'baptized':
                domain.extend([('active', '=', True), ('x_baptized', '=', True)])
            elif record.criteria == 'not_baptized':
                domain.extend([('active', '=', True), ('x_baptized', '=', False)])
            elif record.criteria == 'assembly':
                domain.extend([('active', '=', True), ('x_applies_for_assembly', '=', True)])
            # 'all' implies no additional active filtering or baptized filtering, just all church members
            
            # Find members
            members = self.env['res.partner'].search(domain, order='name asc')
            
            # Prepare new lines
            new_lines = [(5, 0, 0)] # Command 5 clears existing records
            for member in members:
                new_lines.append((0, 0, {
                    'partner_id': member.id,
                    'status': 'no',
                }))
            record.write({'line_ids': new_lines})

    @api.onchange('criteria')
    def _onchange_criteria(self):
        # We can simulate the reloading in the UI by using `update` or directly changing line_ids
        domain = [('x_is_church_member', '=', True)]
        
        if self.criteria == 'active':
            domain.append(('active', '=', True))
        elif self.criteria == 'baptized':
            domain.extend([('active', '=', True), ('x_baptized', '=', True)])
        elif self.criteria == 'not_baptized':
            domain.extend([('active', '=', True), ('x_baptized', '=', False)])
        elif self.criteria == 'assembly':
            domain.extend([('active', '=', True), ('x_applies_for_assembly', '=', True)])
            
        members = self.env['res.partner'].search(domain, order='name asc')
        
        new_lines = [(5, 0, 0)]
        for member in members:
            new_lines.append((0, 0, {
                'partner_id': member.id,
                'status': 'no',
            }))
        self.line_ids = new_lines

    def action_open(self):
        self.write({'state': 'abierto'})

    def action_close(self):
        self.write({'state': 'cerrado'})

    def action_draft(self):
        self.write({'state': 'pendiente'})

    def action_refresh_members(self):
        self.ensure_one()
        if self.state == 'cerrado':
            return
            
        # Current members in lines
        existing_partner_ids = self.line_ids.mapped('partner_id').ids
        
        # Current active church members
        members = self.env['res.partner'].search([
            ('x_is_church_member', '=', True),
            ('active', '=', True),
            ('id', 'not in', existing_partner_ids)
        ])
        
        if members:
            new_lines = []
            for member in members:
                new_lines.append((0, 0, {
                    'partner_id': member.id,
                    'status': 'no',
                }))
            self.write({'line_ids': new_lines})
        
        # Also, check if we should remove members who NO LONGER are active or church members
        # but only if their status is still 'no' (to avoid losing manually set data)
        obsolete_lines = self.line_ids.filtered(
            lambda l: (not l.partner_id.x_is_church_member or not l.partner_id.active) 
            and l.status == 'no'
        )
        if obsolete_lines:
            obsolete_lines.unlink()
            
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
