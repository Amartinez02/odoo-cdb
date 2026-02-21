from odoo import api, models, tools


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    @tools.ormcache('frozenset(self.env.user._get_group_ids())', 'frozenset(self.env.user.hide_menu_ids.ids)', 'debug')
    def _visible_menu_ids(self, debug=False):
        res = super(IrUiMenu, self)._visible_menu_ids(debug)

        hidden_menus = self.env.user.hide_menu_ids
        if not hidden_menus:
            return res

        # Convert frozenset to set for manipulation, then remove hidden menus
        visible = set(res) - set(hidden_menus.ids)

        # Get all menus that are in our visible set
        all_menus = self.browse(visible)
        action_menus = all_menus.filtered(lambda m: m.action)

        final_menus = set()
        for menu in action_menus:
            final_menus.add(menu.id)
            parent = menu.parent_id
            while parent and parent.id in visible and parent.id not in final_menus:
                final_menus.add(parent.id)
                parent = parent.parent_id

        return frozenset(final_menus)
