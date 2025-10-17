from odoo import fields, models  # type: ignore

class ResPartner(models.Model):
    _inherit = "res.partner"

    odoogpt_channel_id = fields.Many2one("discuss.channel")
