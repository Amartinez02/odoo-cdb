{
    'name': 'Church Management (CDB)',
    'version': '1.0',
    'summary': 'Manage church members, ministries, roles, and family connections.',
    'description': """
Church Membership Management
============================
This module allows for the detailed management of church members, including:
- Personal data (gender, education, occupation).
- Church data (baptism, entry date, ministries).
- Family connections.
- Custom views for church members.
    """,
    'category': 'Human Resources',
    'author': 'Antigravity / Anthony Martinez',
    'website': 'https://github.com/Amartinez02/odoo-cdb',
    'depends': ['base', 'mail', 'contacts'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/church_menus.xml',
        'views/res_partner_views.xml',
        'views/church_attendance_views.xml',
        'views/church_attendance_report_views.xml',
        'views/church_activity_views.xml',
        'views/dashboard_views.xml',
        'views/config_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'cdb_management/static/src/css/cdb_management.css',
        ],
    },
    'application': True,
    'installable': True,
    'license': 'LGPL-3',
}
