{
    "name": "OdooGPT",
    "version": "17.0.0.0.1",
    "summary": "Odoo integration with openai",
    "category": "Productivity/Discuss",
    "author": "Osliani Figueiras",
    "website": "",
    "license": "OPL-1",
    "depends": ["base", "mail", "calendar", "survey"],
    "external_dependencies": {
        "python": [
            "openai",
            "python-dotenv",
            "psycopg2-binary",
            "phonenumbers",
            "flanker",
            "markdown2",
            "markupsafe",
            "PyPDF2",
            "python-docx",
            "openpyxl",
            "python-dateutil",
        ]
    },
    "data": [
        "security/ir.model.access.csv",
        "data/res_partner.xml",
        "data/res_users.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "odoogpt/static/src/css/odoo_gpt_messages.css",
        ],
    },
    "installable": True,
    "auto_install": False,
}
