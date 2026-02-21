import json
from datetime import datetime

from odoo import http
from odoo.http import request


class CdbElectionController(http.Controller):

    # ── Helper ─────────────────────────────────────────────────────────

    def _get_election_data(self, election):
        """Build the JSON-serializable data structure for an election."""
        positions = []
        for pos in election.position_ids.sorted('sequence'):
            candidates = []
            sorted_cands = pos.candidate_ids.sorted(
                key=lambda c: (-c.votes, c.sequence)
            )
            for rank, cand in enumerate(sorted_cands, start=1):
                candidates.append({
                    'id': cand.id,
                    'partner_id': cand.partner_id.id,
                    'name': cand.partner_id.name or '',
                    'votes': cand.votes,
                    'percentage': round(cand.percentage, 1),
                    'is_winner': cand.is_winner,
                    'rank': cand.winner_rank if cand.winner_rank else rank,
                })
            positions.append({
                'id': pos.id,
                'name': pos.name,
                'winners_count': pos.winners_count,
                'total_votes': pos.total_position_votes,
                'candidates': candidates,
            })
        return positions

    def _get_company_logo(self):
        """Return the company logo URL or False."""
        company = request.env.company
        if company.logo:
            return f'/web/image/res.company/{company.id}/logo'
        return False

    # ── Live Voting Board ──────────────────────────────────────────────

    @http.route(
        '/cdb/elections/<int:election_id>',
        type='http', auth='public', website=False,
    )
    def election_live_board(self, election_id, **kwargs):
        election = request.env['cdb.election'].sudo().browse(election_id)
        if not election.exists():
            return request.not_found()

        positions = self._get_election_data(election)
        values = {
            'election': election,
            'positions': positions,
            'company_logo': self._get_company_logo(),
        }
        return request.render(
            'cdb_management_elections.cdb_election_live', values
        )

    # ── JSON Data Endpoint ─────────────────────────────────────────────

    @http.route(
        '/cdb/elections/<int:election_id>/data',
        type='http', auth='public', website=False,
        methods=['GET'],
    )
    def election_data_json(self, election_id, **kwargs):
        election = request.env['cdb.election'].sudo().browse(election_id)
        if not election.exists():
            return request.not_found()

        positions = self._get_election_data(election)
        data = {
            'election_id': election.id,
            'name': election.name,
            'state': election.state,
            'total_votes': election.total_votes,
            'positions': positions,
        }
        return request.make_json_response(data)

    # ── Published Results Page ─────────────────────────────────────────

    @http.route(
        '/cdb/elections/<int:election_id>/results',
        type='http', auth='public', website=False,
    )
    def election_results_page(self, election_id, **kwargs):
        election = request.env['cdb.election'].sudo().browse(election_id)
        if not election.exists():
            return request.not_found()

        if election.state != 'published':
            return request.not_found()

        positions = self._get_election_data(election)
        values = {
            'election': election,
            'positions': positions,
            'company_logo': self._get_company_logo(),
            'publish_date': (
                election.date_end.strftime('%d/%m/%Y %H:%M')
                if election.date_end else
                datetime.now().strftime('%d/%m/%Y %H:%M')
            ),
        }
        return request.render(
            'cdb_management_elections.cdb_election_results', values
        )
