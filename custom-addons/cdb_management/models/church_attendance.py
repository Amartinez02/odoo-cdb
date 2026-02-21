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
    responsible_id = fields.Many2one('res.partner', string='Responsible', 
                                    default=lambda self: self.env.user.partner_id, tracking=True)
    
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
        self.ensure_one()
        # Find all active church members
        members = self.env['res.partner'].search([
            ('x_is_church_member', '=', True),
            ('active', '=', True)
        ], order='name asc') # Name is "Apellido Nombre" or similar in Odoo by default, but we'll trust the search order
        
        # Sort manually by name to be sure (Odoo name usually stores full name)
        # If user wants specific "Apellido, Nombre" sorting, we might need to be careful
        # Odoo partners are usually searched by name.
        
        lines = []
        for member in members:
            lines.append((0, 0, {
                'partner_id': member.id,
                'status': 'no', # Default to 'No' or keep empty? User said dropdown to place Si, No, Excusa.
            }))
        self.write({'line_ids': lines})

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
