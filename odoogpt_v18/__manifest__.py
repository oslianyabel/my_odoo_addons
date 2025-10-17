{
    "name": "OdooGPT",
    "version": "18.0.0.0.1",
    "summary": "Odoo integration with OpenAI",
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
            "markdown2",
            "markupsafe",
            "flanker",
            "PyPDF2",
            "python-docx",
            "openpyxl",
        ]
    },
    "data": [
        "security/ir.model.access.csv",
        "data/res_partner.xml",
        "data/res_users.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "odoogpt/static/src/views/list/list_controller.js",
            "odoogpt/static/src/views/list/list_controller.xml",
            "odoogpt/static/src/css/odoo_gpt_messages.css",
        ],
    },
    "installable": True,
    "auto_install": False,
}
