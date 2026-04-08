from odoo import models, fields

class ChurchRole(models.Model):
    _name = 'church.role'
    _description = 'Church role'
    _order = 'name'

    name = fields.Char(string='Role name', required=True)
    active = fields.Boolean(default=True)
    description = fields.Text(string='Description')
    color = fields.Integer(string='Color')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )
