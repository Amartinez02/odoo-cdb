from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class CdbElection(models.Model):
    _name = 'cdb.election'
    _description = 'Church election'
    _order = 'date_start desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True, tracking=True)
    date_start = fields.Datetime(string='Start date', tracking=True)
    date_end = fields.Datetime(string='End date', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('published', 'Published'),
    ], string='State', default='draft', required=True, tracking=True)
    description = fields.Html(string='Description')

    position_ids = fields.One2many(
        'cdb.election.position', 'election_id', string='Positions')
    candidate_ids = fields.One2many(
        'cdb.election.candidate', 'election_id', string='Candidates')

    total_votes = fields.Integer(
        string='Total votes', compute='_compute_totals', store=True)
    total_candidates = fields.Integer(
        string='Total candidates', compute='_compute_totals', store=True)

    @api.depends('candidate_ids.votes')
    def _compute_totals(self):
        for election in self:
            election.total_votes = sum(election.candidate_ids.mapped('votes'))
            election.total_candidates = len(election.candidate_ids)

    # ── State transitions ──────────────────────────────────────────────

    def action_open(self):
        for election in self:
            if election.state != 'draft':
                raise UserError("Only draft elections can be opened.")
            if not election.position_ids:
                raise UserError(
                    "Cannot open an election without positions. "
                    "Please add at least one position first."
                )
            if not election.candidate_ids:
                raise UserError(
                    "Cannot open an election without candidates. "
                    "Please assign candidates to positions first."
                )
            election.state = 'open'

    def action_close(self):
        for election in self:
            if election.state != 'open':
                raise UserError("Only open elections can be closed.")
            election.state = 'closed'
            election._compute_winners()

    def action_publish(self):
        for election in self:
            if election.state != 'closed':
                raise UserError("Only closed elections can be published.")
            election.state = 'published'

    def action_reset_draft(self):
        for election in self:
            election.state = 'draft'
            # Reset winner flags
            election.candidate_ids.write({
                'is_winner': False,
                'winner_rank': 0,
            })

    # ── Winner computation ─────────────────────────────────────────────

    def _compute_winners(self):
        """Compute winners for each position based on votes descending."""
        for election in self:
            for position in election.position_ids:
                candidates = position.candidate_ids.sorted(
                    key=lambda c: (-c.votes, c.sequence)
                )
                winners_count = min(
                    position.winners_count, len(candidates)
                )
                for rank, candidate in enumerate(candidates, start=1):
                    candidate.write({
                        'winner_rank': rank,
                        'is_winner': rank <= winners_count,
                    })

    # ── Results URL ────────────────────────────────────────────────────

    def action_view_results(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/cdb/elections/{self.id}/results',
            'target': 'new',
        }

    def action_view_live(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/cdb/elections/{self.id}',
            'target': 'new',
        }


class CdbElectionPosition(models.Model):
    _name = 'cdb.election.position'
    _description = 'Election position'
    _order = 'sequence, id'

    election_id = fields.Many2one(
        'cdb.election', string='Election', required=True, ondelete='cascade')
    name = fields.Char(string='Position', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    winners_count = fields.Integer(string='Winners', default=1)
    candidate_ids = fields.One2many(
        'cdb.election.candidate', 'position_id', string='Candidates')
    total_position_votes = fields.Integer(
        string='Total votes', compute='_compute_total_position_votes',
        store=True)

    @api.depends('candidate_ids.votes')
    def _compute_total_position_votes(self):
        for position in self:
            position.total_position_votes = sum(
                position.candidate_ids.mapped('votes'))


class CdbElectionCandidate(models.Model):
    _name = 'cdb.election.candidate'
    _description = 'Election candidate'
    _order = 'position_id, sequence, id'

    election_id = fields.Many2one(
        'cdb.election', string='Election', required=True, ondelete='cascade')
    position_id = fields.Many2one(
        'cdb.election.position', string='Position', required=True,
        ondelete='cascade',
        domain="[('election_id', '=', election_id)]")
    partner_id = fields.Many2one(
        'res.partner', string='Candidate', required=True,
        domain="[('x_is_church_member', '=', True)]")
    sequence = fields.Integer(string='Sequence', default=10)
    votes = fields.Integer(string='Votes', default=0)
    election_state = fields.Selection(
        related='election_id.state', string='Election state', store=False)
    percentage = fields.Float(
        string='%', compute='_compute_percentage', store=True,
        digits=(5, 2))
    is_winner = fields.Boolean(string='Winner', default=False)
    winner_rank = fields.Integer(string='Rank', default=0)

    _sql_constraints = [
        ('unique_candidate_per_election',
         'UNIQUE(election_id, partner_id)',
         'A candidate can only run for one position per election.'),
    ]

    @api.constrains('position_id', 'election_id')
    def _check_position_election(self):
        for candidate in self:
            if candidate.position_id.election_id != candidate.election_id:
                raise ValidationError(
                    "The position must belong to the same election as the "
                    "candidate."
                )

    @api.depends('votes', 'position_id.total_position_votes')
    def _compute_percentage(self):
        for candidate in self:
            total = candidate.position_id.total_position_votes
            if total > 0:
                candidate.percentage = (candidate.votes / total) * 100
            else:
                candidate.percentage = 0.0

    # ── Vote actions ───────────────────────────────────────────────────

    def action_add_vote(self):
        self.ensure_one()
        if self.election_id.state != 'open':
            raise UserError("Votes can only be cast while the election is open.")
        self.sudo().write({'votes': self.votes + 1})
        self.env['cdb.election.vote.log'].sudo().create({
            'election_id': self.election_id.id,
            'candidate_id': self.id,
            'action': 'add',
            'delta': 1,
            'user_id': self.env.uid,
        })
        # Notify bus channel for live updates
        self._send_bus_notification()

    def action_subtract_vote(self):
        self.ensure_one()
        if self.election_id.state != 'open':
            raise UserError("Votes can only be modified while the election is open.")
        if self.votes <= 0:
            raise UserError("Votes cannot go below zero.")
        self.sudo().write({'votes': self.votes - 1})
        self.env['cdb.election.vote.log'].sudo().create({
            'election_id': self.election_id.id,
            'candidate_id': self.id,
            'action': 'subtract',
            'delta': -1,
            'user_id': self.env.uid,
        })
        self._send_bus_notification()

    def _send_bus_notification(self):
        """Send a bus notification so the live board refreshes."""
        channel = f'cdb_election_{self.election_id.id}'
        self.env['bus.bus']._sendone(channel, 'cdb_election_update', {
            'election_id': self.election_id.id,
        })


class CdbElectionVoteLog(models.Model):
    _name = 'cdb.election.vote.log'
    _description = 'Election vote log'
    _order = 'create_date desc'

    election_id = fields.Many2one(
        'cdb.election', string='Election', required=True, ondelete='cascade')
    candidate_id = fields.Many2one(
        'cdb.election.candidate', string='Candidate', required=True,
        ondelete='cascade')
    action = fields.Selection([
        ('add', 'Add'),
        ('subtract', 'Subtract'),
    ], string='Action', required=True)
    delta = fields.Integer(string='Delta')
    user_id = fields.Many2one(
        'res.users', string='User', default=lambda self: self.env.uid)
