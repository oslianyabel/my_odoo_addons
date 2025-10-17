from odoo import api, fields, models  # type: ignore


class DiscussChannel(models.Model):
    _inherit = "discuss.channel"

    is_odoogpt_chat = fields.Boolean(compute="_compute_is_odoogpt_chat")
    view_data = fields.Json(copy=False)

    @api.depends("is_chat", "channel_partner_ids")
    def _compute_is_odoogpt_chat(self):
        odoogpt = self.env.ref("odoogpt.partner_odoogpt")
        for channel in self:
            channel.is_odoogpt_chat = bool(
                channel.is_chat and odoogpt.id in channel.channel_partner_ids.ids
            )
