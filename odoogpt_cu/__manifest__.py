{
    "name": "OdooGPT",
    "version": "17.0.0.0.1",
    "summary": "Odoo integration with OpenAI",
    "category": "Productivity/Discuss",
    "author": "Osliani - Soluciones DTeam",
    "website": "https://www.dteam.cu",
    "license": "OPL-1",
    "depends": ["base", "mail", "calendar", "survey"],
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
