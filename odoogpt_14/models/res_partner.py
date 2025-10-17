from odoo import fields, models
import json

class ResPartner(models.Model):
    _inherit = "res.partner"

    odoogpt_channel_id = fields.Many2one("mail.channel")

    def open_odoogpt(self, params):
        partner = self.env.user.partner_id
        odoogpt = self.env.ref("odoogpt.odoogpt_user")
        
        if not partner.odoogpt_channel_id:
            channel_id = (
                self.env["mail.channel"]
                .with_context(mail_create_nosubscribe=True)
                .sudo()
                .create({
                    "name": odoogpt.partner_id.name,
                    "channel_type": "chat",
                    "public": "private",
                    "channel_partner_ids": [(4, odoogpt.partner_id.id), (4, partner.id)],
                    "view_data": json.dumps(params) if params else False,
                })
            )
            partner.odoogpt_channel_id = channel_id
        else:
            partner.odoogpt_channel_id.write({"view_data": json.dumps(params) if params else False})

        return odoogpt.id
