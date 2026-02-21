from odoo import models, fields, api

class ChurchFamilyRelation(models.Model):
    _name = 'church.family.relation'
    _description = 'Church family relation'

    partner_id = fields.Many2one('res.partner', string='Member', ondelete='cascade', required=True)
    relation_type = fields.Selection([
        ('hijo', 'Son'),
        ('hija', 'Daughter'),
        ('madre', 'Mother'),
        ('padre', 'Father'),
        ('esposa', 'Wife'),
        ('esposo', 'Husband')
    ], string='Relationship type', required=True)
    
    is_member = fields.Boolean(string='Is member', default=True)
    related_partner_id = fields.Many2one('res.partner', string='Relative (member)', 
                                        domain=[('x_is_church_member', '=', True)])
    non_member_name = fields.Char(string='Name (non member)')
    x_birthdate = fields.Date(string='Birthdate', compute='_compute_x_birthdate', inverse='_inverse_x_birthdate', store=True)

    @api.depends('is_member', 'related_partner_id.x_birthdate')
    def _compute_x_birthdate(self):
        for record in self:
            if record.is_member and record.related_partner_id:
                record.x_birthdate = record.related_partner_id.x_birthdate
            elif not record.is_member and not record.x_birthdate:
                record.x_birthdate = False

    def _inverse_x_birthdate(self):
        for record in self:
            if record.is_member and record.related_partner_id:
                record.related_partner_id.x_birthdate = record.x_birthdate

    @api.onchange('is_member')
    def _onchange_is_member(self):
        if self.is_member:
            self.non_member_name = False
        else:
            self.related_partner_id = False
