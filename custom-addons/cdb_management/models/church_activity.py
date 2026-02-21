from odoo import models, fields

class ChurchActivity(models.Model):
    _name = 'church.activity'
    _description = 'Yearly Activity'
    _order = 'date desc, id desc'

    name = fields.Char(string='Activity Name', required=True)
    date = fields.Date(string='Date', required=True)
    responsible = fields.Char(string='Responsible')
    active = fields.Boolean(default=True)
