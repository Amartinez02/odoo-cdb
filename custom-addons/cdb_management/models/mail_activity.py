"""Extend mail.activity with company_id for multi-company filtering.

When an activity is linked to a cdb_ record (or any record with company_id),
the activity's company_id is resolved from the parent record.  This lets the
global "Activities" view and activity calendar be filtered by company so
users never see activities from the wrong company.
"""

from odoo import models, fields, api


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    company_id = fields.Many2one(
        'res.company', string='Company',
        compute='_compute_company_id', store=True,
        index=True,
    )

    @api.depends('res_model', 'res_id')
    def _compute_company_id(self):
        """Resolve the company from the record this activity is attached to."""
        for activity in self:
            record = activity._get_activity_record()
            if record and hasattr(record, 'company_id') and record.company_id:
                activity.company_id = record.company_id
            else:
                activity.company_id = False

    def _get_activity_record(self):
        """Return the record this activity is attached to, if it exists."""
        self.ensure_one()
        if not self.res_model or not self.res_id:
            return None
        try:
            return self.env[self.res_model].browse(self.res_id).exists()
        except KeyError:
            return None
