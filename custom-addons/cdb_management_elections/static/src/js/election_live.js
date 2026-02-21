/**
 * CDB Elections – Live Board Real-time Updates
 * Optimized Version: Updates values and sorts candidates in real-time.
 */
(function () {
    'use strict';

    function init() {
        if (window.cdb_election_init_done) return;
        window.cdb_election_init_done = true;

        var boardEl = document.querySelector('.cdb-board');
        if (!boardEl) return;
        var electionId = parseInt(boardEl.dataset.electionId, 10);
        if (!electionId) return;

        var DATA_URL = '/cdb/elections/' + electionId + '/data';
        var currentState = boardEl.dataset.state || 'open';

        function showWinners() {
            return currentState === 'closed' || currentState === 'published';
        }

        /**
         * partialUpdateBoard: Updates values and reorders candidates.
         */
        function partialUpdateBoard(positions) {
            var container = document.getElementById('cdb-positions-data');
            if (!container) return;

            positions.forEach(function (pos) {
                var card = container.querySelector('.cdb-pos-card[data-position-id="' + pos.id + '"]');
                if (!card) return;

                // 1. Update Position Total
                var strongTotal = card.querySelector('.cdb-pos-foot strong');
                if (strongTotal && strongTotal.textContent != pos.total_votes) {
                    strongTotal.textContent = pos.total_votes;
                }

                // 2. Process Candidates
                if (!pos.candidates) return;
                
                var candsListContainer = card.querySelector('.cdb-cands');
                if (!candsListContainer) return;

                // Sort candidates by votes (descending) before updating DOM order
                var sortedCandidates = pos.candidates.slice().sort(function(a, b) {
                    return b.votes - a.votes;
                });

                sortedCandidates.forEach(function (c) {
                    var row = candsListContainer.querySelector('.cdb-cand[data-candidate-id="' + c.id + '"]');
                    if (!row) return;

                    // Update Votes
                    var voteNum = row.querySelector('.cdb-vote-num');
                    if (voteNum && voteNum.textContent != c.votes) {
                        voteNum.classList.remove('cdb-flash');
                        void voteNum.offsetWidth; // Trigger reflow
                        voteNum.classList.add('cdb-flash');
                        voteNum.textContent = c.votes;
                    }

                    // Update Percentage & Progress Bar
                    var pctVal = c.percentage.toFixed(1);
                    var pctText = row.querySelector('.cdb-pct');
                    if (pctText && pctText.textContent != pctVal + '%') {
                        pctText.textContent = pctVal + '%';
                    }

                    var fill = row.querySelector('.cdb-fill');
                    if (fill) {
                        fill.style.width = c.percentage + '%';
                    }

                    // Update Winner Status
                    var isWinnerNow = c.is_winner && showWinners();
                    var wasWinner = row.classList.contains('winner');
                    if (isWinnerNow !== wasWinner) {
                        if (isWinnerNow) {
                            row.classList.add('winner');
                            var nameDiv = row.querySelector('.cdb-name');
                            if (nameDiv && !nameDiv.querySelector('.cdb-elected-badge')) {
                                var badge = document.createElement('span');
                                badge.className = 'cdb-elected-badge';
                                badge.textContent = '\u2B50 Electo';
                                nameDiv.appendChild(document.createTextNode(' '));
                                nameDiv.appendChild(badge);
                            }
                        } else {
                            row.classList.remove('winner');
                            var badge = row.querySelector('.cdb-elected-badge');
                            if (badge) badge.remove();
                        }
                    }

                    // 3. Live Reordering: Append the row to the container in the new sorted order.
                    // appendChild moves the element if it already exists in the DOM.
                    candsListContainer.appendChild(row);
                });
            });
        }

        function updateTotal(t) {
            var el = document.querySelector('.cdb-total-pill strong');
            if (el && el.textContent != t) el.textContent = t;
        }

        function refresh() {
            fetch(DATA_URL, { headers: { Accept: 'application/json' } })
                .then(function (r) { return r.json(); })
                .then(function (d) {
                    currentState = d.state || currentState;
                    boardEl.dataset.state = currentState;
                    updateTotal(d.total_votes);
                    partialUpdateBoard(d.positions);
                })
                .catch(function (e) {
                    console.warn('CDB refresh error', e);
                });
        }

        // 5. Accordion Logic: Click header to expand/collapse
        // Use document-level delegation to be extremely robust
        document.addEventListener('click', function(e) {
            var trigger = e.target.closest('.cdb-accordion-trigger');
            if (!trigger) return;

            e.preventDefault();
            e.stopPropagation();

            var card = trigger.closest('.cdb-pos-card');
            if (card) {
                var isCollapsed = card.classList.contains('collapsed');
                console.log('CDB: Toggling card', card.dataset.positionId, 'Current status collapsed:', isCollapsed);
                card.classList.toggle('collapsed');
            }
        }, true); // Use capture phase to be even more sure

        setInterval(refresh, 3000);
        console.log('CDB Election Live Board (Accordion Ready) ready', electionId);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
