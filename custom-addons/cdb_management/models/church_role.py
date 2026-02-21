from odoo import models, fields

class ChurchRole(models.Model):
    _name = 'church.role'
    _description = 'Church role'
    _order = 'name'

    name = fields.Char(string='Role name', required=True)
    active = fields.Boolean(default=True)
    description = fields.Text(string='Description')
    color = fields.Integer(string='Color')
