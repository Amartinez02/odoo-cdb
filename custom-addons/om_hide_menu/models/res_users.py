# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    hide_menu_ids = fields.Many2many('ir.ui.menu','hide_menu_users_rel', string="Hide Menus")

    def write(self, vals):
        res = super().write(vals)
        if 'hide_menu_ids' in vals:
            self.env.registry.clear_cache()
        return res

