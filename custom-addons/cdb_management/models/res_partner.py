from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date

class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_is_church_member = fields.Boolean(string='Is church member', default=False)

    # Naming
    x_first_name = fields.Char(string='First name')
    x_last_name = fields.Char(string='Last name')

    @api.depends('x_first_name', 'x_last_name')
    def _compute_display_name(self):
        """Override display_name compute to use first+last for persons."""
        for partner in self:
            if partner.company_type == 'person' and (partner.x_first_name or partner.x_last_name):
                partner.display_name = (
                    f"{partner.x_first_name or ''} {partner.x_last_name or ''}"
                ).strip()
            else:
                super(ResPartner, partner)._compute_display_name()

    @api.onchange('x_first_name', 'x_last_name')
    def _onchange_first_last_name(self):
        """Auto-concatenate first + last name into the name field for persons."""
        if self.company_type == 'person' and (self.x_first_name or self.x_last_name):
            self.name = (
                f"{self.x_first_name or ''} {self.x_last_name or ''}"
            ).strip()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._sync_name_from_parts(vals)
        return super().create(vals_list)

    def write(self, vals):
        # If writing first/last name, recompute name
        if 'x_first_name' in vals or 'x_last_name' in vals:
            for record in self:
                if record.company_type == 'person':
                    first = vals.get('x_first_name', record.x_first_name) or ''
                    last = vals.get('x_last_name', record.x_last_name) or ''
                    vals['name'] = f"{first} {last}".strip()
        # If writing name directly (e.g. import), try to split into first/last
        if 'name' in vals and 'x_first_name' not in vals and 'x_last_name' not in vals:
            for record in self:
                if record.company_type == 'person':
                    parts = (vals['name'] or '').strip().split(' ', 1)
                    vals['x_first_name'] = parts[0] if parts else ''
                    vals['x_last_name'] = parts[1] if len(parts) > 1 else ''
        return super().write(vals)

    @api.model
    def _sync_name_from_parts(self, vals):
        """Synchronize name from first/last or vice versa on create."""
        is_person = vals.get('company_type', 'person') == 'person'
        has_parts = vals.get('x_first_name') or vals.get('x_last_name')
        if is_person and has_parts:
            first = vals.get('x_first_name', '') or ''
            last = vals.get('x_last_name', '') or ''
            vals['name'] = f"{first} {last}".strip()
        elif is_person and vals.get('name') and not has_parts:
            # Best-effort split from name
            parts = vals['name'].strip().split(' ', 1)
            vals['x_first_name'] = parts[0] if parts else ''
            vals['x_last_name'] = parts[1] if len(parts) > 1 else ''

    @api.constrains('x_first_name', 'x_last_name', 'company_type', 'x_is_church_member')
    def _check_person_name_required(self):
        for partner in self:
            if (partner.company_type == 'person'
                    and partner.x_is_church_member
                    and (not partner.x_first_name or not partner.x_last_name)):
                raise ValidationError(
                    "Church members must have both first name and last name."
                )

    # Personal Data
    x_gender = fields.Selection([
        ('masculino', 'Male'),
        ('femenino', 'Female')
    ], string='Gender')
    x_education_level = fields.Selection([
        ('primaria', 'Primary'),
        ('secundaria', 'Secondary/high school'),
        ('tecnico', 'Technical'),
        ('universitario', 'University'),
        ('maestria', 'Master'),
        ('doctorado', 'Doctorate')
    ], string='Education level')
    x_occupational_status = fields.Selection([
        ('estudiante', 'Student'),
        ('empleado_privado', 'Private employee'),
        ('empleado_publico', 'Public employee'),
        ('independiente', 'Independent'),
        ('desempleado', 'Unemployed'),
        ('hogar', 'Home'),
        ('jubilado', 'Retired')
    ], string='Occupational status')
    x_current_occupation = fields.Char(string='Current occupation')
    x_marital_status = fields.Selection([
        ('soltero', 'Single'),
        ('casado', 'Married'),
        ('union_libre', 'Free union'),
        ('divorciado', 'Divorced'),
        ('viudo', 'Widower')
    ], string='Marital status')

    x_birthdate = fields.Date(string='Birthdate')
    mobile = fields.Char(string='Mobile')

    # Dashboard Helpers
    x_birthday_month = fields.Integer(string='Birthday month', compute='_compute_birthday_parts', store=True)
    x_birthday_day = fields.Integer(string='Birthday day', compute='_compute_birthday_parts', store=True)

    # Computed Age
    x_age = fields.Integer(string='Age', compute='_compute_x_age', store=True)

    # Sector
    x_sector = fields.Char(string='Sector')

    # Church Data
    x_baptized = fields.Boolean(string='Baptized')
    x_baptism_date = fields.Date(string='Baptism date')
    x_church_entry_date = fields.Date(string='Entry date (CDB)')
    x_ministry_ids = fields.Many2many('church.ministry', 'church_member_ministry_rel', 'partner_id', 'ministry_id', string='Ministries')
    x_role_ids = fields.Many2many('church.role', 'church_member_role_rel', 'partner_id', 'role_id', string='Roles')
    x_interested_ministry_ids = fields.Many2many('church.ministry', 'church_member_interest_rel', 'partner_id', 'ministry_id', string='Interested ministries')

    # Invitations & Discipleship
    x_invited_by_id = fields.Many2one('res.partner', string='Invited by', domain=[('x_is_church_member', '=', True)])
    x_discipler_id = fields.Many2one('res.partner', string='Discipler', domain=[('x_is_church_member', '=', True)])

    # Family
    x_family_relation_ids = fields.One2many('church.family.relation', 'partner_id', string='Family relations')

    @api.depends('x_birthdate')
    def _compute_x_age(self):
        today = date.today()
        for record in self:
            if record.x_birthdate:
                birthdate = record.x_birthdate
                record.x_age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
            else:
                record.x_age = 0

    @api.depends('x_birthdate')
    def _compute_birthday_parts(self):
        for record in self:
            if record.x_birthdate:
                record.x_birthday_month = record.x_birthdate.month
                record.x_birthday_day = record.x_birthdate.day
            else:
                record.x_birthday_month = 0
                record.x_birthday_day = 0

