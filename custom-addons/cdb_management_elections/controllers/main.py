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
        type='http', auth='public',
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
            'languages': [],  # Fallback for portal.language_selector
            'no_footer': True, # Skip footer rendering to avoid language selector issues
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
        type='http', auth='public',
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
            'languages': [],  # Fallback for portal.language_selector
            'no_footer': True, # Skip footer rendering
            'publish_date': (
                election.date_end.strftime('%d/%m/%Y %H:%M')
                if election.date_end else
                datetime.now().strftime('%d/%m/%Y %H:%M')
            ),
        }
        return request.render(
            'cdb_management_elections.cdb_election_results', values
        )

    # ── QR Voting Page (By Position) ───────────────────────────────────

    @http.route(
        '/cdb/elections/<int:election_id>/vote/position/<int:position_id>',
        type='http', auth='public',
    )
    def election_vote_page(self, election_id, position_id, **kwargs):
        election = request.env['cdb.election'].sudo().browse(election_id)
        if not election.exists():
            return request.not_found()

        position = request.env['cdb.election.position'].sudo().browse(
            position_id
        )
        if not position.exists() or position.election_id.id != election_id:
            return request.not_found()

        values = {
            'election': election,
            'position': position,
            'company_logo': self._get_company_logo(),
            'is_open': election.state == 'open',
            'languages': [],
            'no_footer': True,
        }
        return request.render(
            'cdb_management_elections.cdb_election_vote', values
        )

    # ── Vote Submission (JSON, By Position) ────────────────────────────

    @http.route(
        '/cdb/elections/<int:election_id>/vote/position/<int:position_id>/submit',
        type='json', auth='public', methods=['POST'],
    )
    def election_vote_submit(self, election_id, position_id, **kwargs):
        voter_code = kwargs.get('voter_code', '')
        candidate_ids = kwargs.get('candidate_ids', [])

        election = request.env['cdb.election'].sudo().browse(election_id)
        if not election.exists():
            return {'success': False, 'message': 'Elección no encontrada.'}

        if election.state != 'open':
            return {
                'success': False,
                'message': 'La votación no está abierta.',
            }

        position = request.env['cdb.election.position'].sudo().browse(
            position_id
        )
        if not position.exists() or position.election_id.id != election_id:
            return {
                'success': False,
                'message': 'Cargo no válido.',
            }

        # Check candidate list
        if not candidate_ids:
            return {
                'success': False,
                'message': 'Debe seleccionar al menos un candidato.',
            }

        if len(candidate_ids) > position.winners_count:
            return {
                'success': False,
                'message': (
                    f'No puede votar por más de {position.winners_count} '
                    f'candidatos para este cargo.'
                ),
            }

        # Validate voter code
        voter = request.env['cdb.election.voter'].sudo().search([
            ('election_id', '=', election_id),
            ('voter_code', '=', voter_code),
        ], limit=1)
        if not voter:
            return {
                'success': False,
                'message': 'Código de votante inválido.',
            }

        # Check if voter has already voted in this position
        votes_in_position = request.env['cdb.election.vote.log'].sudo().search_count([
            ('election_id', '=', election_id),
            ('voter_id', '=', voter.id),
            ('candidate_id.position_id', '=', position_id),
            ('action', '=', 'add'),
        ])
        if votes_in_position > 0:
            return {
                'success': False,
                'message': (
                    f'Ya has votado para el cargo "{position.name}".'
                ),
            }

        # Verify selected candidates belong to the position
        valid_candidates = position.candidate_ids.filtered(
            lambda c: c.id in candidate_ids
        )
        if len(valid_candidates) != len(candidate_ids):
            return {
                'success': False,
                'message': (
                    'Uno o más candidatos no son válidos para este cargo.'
                ),
            }

        # Register the votes
        for candidate in valid_candidates:
            candidate.sudo().write({'votes': candidate.votes + 1})
            request.env['cdb.election.vote.log'].sudo().create({
                'election_id': election_id,
                'candidate_id': candidate.id,
                'voter_id': voter.id,
                'action': 'add',
                'delta': 1,
            })
            # Send bus notification for live board
            candidate._send_bus_notification()

        # Build list of names for confirmation/feedback
        cand_names = ", ".join(valid_candidates.mapped('partner_id.name'))
        return {
            'success': True,
            'message': (
                f'¡Voto registrado para {cand_names}! Gracias por participar.'
            ),
        }

