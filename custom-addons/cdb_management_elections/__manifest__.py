{
    'name': 'Church Elections (CDB)',
    'version': '1.0',
    'summary': 'Manage church elections, candidates, voting, and results.',
    'description': """
Church Elections Management
===========================
This module extends Church Management (CDB) to provide:
- First Name / Last Name split for contacts
- Full election lifecycle (draft → open → closed → published)
- Position-based candidacies with vote tracking
- Real-time QWeb voting board via bus/longpolling
- Published results page with winner badges
    """,
    'category': 'Human Resources',
    'author': 'Antigravity / Anthony Martinez',
    'website': 'https://github.com/Amartinez02/odoo-cdb',
    'depends': ['cdb_management', 'bus'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',

        'views/election_views.xml',
        'views/election_menus.xml',
        'views/election_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'cdb_management_elections/static/src/css/election.css',
            'cdb_management_elections/static/src/js/election_live.js',
        ],
    },
    'application': False,
    'installable': True,
    'license': 'LGPL-3',
}
