from odoo import fields, models  # type: ignore

class ResPartner(models.Model):
    _inherit = "res.partner"

    odoogpt_channel_id = fields.Many2one("discuss.channel")

    def open_odoogpt(self, params):
        partner = self.env.user.partner_id
        odoogpt = self.env.ref("odoogpt.odoogpt_user")
        
        if not partner.odoogpt_channel_id:
            channel_id = (
                self.env["discuss.channel"]
                .sudo()
                .create({
                    "name": odoogpt.partner_id.name,
                    "channel_type": "chat",  # 🔥 Chat 1:1
                    "channel_partner_ids": [(4, odoogpt.partner_id.id), (4, partner.id)],  # 🔥 Asignar ambos al crear
                    "view_data": params,
                })
            )
            partner.odoogpt_channel_id = channel_id
        else:
            partner.odoogpt_channel_id.write({"view_data": params})

        return odoogpt.id  # (Sigues devolviendo el userId como tú quieres)
