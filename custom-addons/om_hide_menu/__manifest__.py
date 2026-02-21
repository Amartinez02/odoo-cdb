# -*- coding: utf-8 -*-
{
    "name": "Hide Menu User Wise",
    "version": "19.0.1.0.0",
    "summary": "Hide specific menu items for individual users without affecting their group permissions",
    "category": "Tools",
    "author": "OdooMatrix",
    "company": "OdooMatrix",
    "maintainer": "OdooMatrix",
    "license": "LGPL-3",
    "website": "https://www.odoomatrix.com",
    "support": "dev.odoomatrix@gmail.com",
    "depends": ["base"],
    "data": [
        "views/res_users_views.xml",
    ],
    "description": """
Hide Menu User Wise
====================

Hide specific menu items for individual users without modifying their group-based access rights.

Key Features:
-------------
* User-wise menu visibility control
* Hide any menu item for specific users

* Works independently of group permissions
* Preserves underlying access rights (only hides UI menus)
* Easy configuration through user form

Contact:
--------
* Email: dev.odoomatrix@gmail.com
    """,
    "images": [
        "static/description/banner.png"
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}