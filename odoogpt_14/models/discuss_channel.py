from odoo import api, fields, models  # type: ignore


class MailChannel(models.Model):
    _inherit = "mail.channel"

    is_odoogpt_chat = fields.Boolean(compute="_compute_is_odoogpt_chat")
    view_data = fields.Text(copy=False)  # Odoo 14 no tiene tipo Json en todos los casos

    @api.depends("channel_type", "channel_partner_ids")
    def _compute_is_odoogpt_chat(self):
        odoogpt = self.env.ref("odoogpt.partner_odoogpt")
        for channel in self:
            channel.is_odoogpt_chat = bool(
                channel.channel_type == 'chat' and odoogpt.id in channel.channel_partner_ids.ids
            )
