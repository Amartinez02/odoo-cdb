{
    'name': 'Login Style (CDB)',
    'version': '1.0',
    'summary': 'Customized login page for ACYM Casa de Bendición',
    'author': 'Antigravity',
    'category': 'Website',
    'depends': ['web', 'auth_signup'],
    'data': [
        'views/login_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'cdb_login_style/static/src/css/login_style.css',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
