from odoo import models, fields

class ChurchMinistry(models.Model):
    _name = 'church.ministry'
    _description = 'Church ministry'
    _order = 'name'

    name = fields.Char(string='Ministry name', required=True)
    active = fields.Boolean(default=True)
    description = fields.Text(string='Description')
    color = fields.Integer(string='Color')
