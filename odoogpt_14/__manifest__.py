{
    "name": "OdooGPT",
    "version": "14.0.0.0.1",
    "summary": "Odoo integration with openai",
    "category": "Productivity/Discuss",
    "author": "JUMO Technologies S.L.",
    "website": "https://www.jumotech.com",
    "license": "OPL-1",
    "depends": ["mail", "queue_job"],
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
        ]
    },
    "data": [
        "security/ir.model.access.csv",
        "data/res_partner.xml",
        "data/res_users.xml",
        "views/main_menu.xml",
        "views/odoogpt_table.xml",
    ],
    "qweb": [
        "static/src/views/list/list_controller.xml",
    ],
    "installable": True,
    "auto_install": False,
}
