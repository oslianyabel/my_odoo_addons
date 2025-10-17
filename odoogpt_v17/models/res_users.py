from odoo import fields, models  # type: ignore


class ResUsers(models.Model):
    _inherit = "res.users"

    last_view_model = fields.Char()
