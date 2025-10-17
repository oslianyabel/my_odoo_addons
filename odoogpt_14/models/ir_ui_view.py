from odoo import models  # type: ignore


class IrUiView(models.Model):
    _inherit = "ir.ui.view"

    def _get_combined_arch(self):
        """Save the last view model requested"""
        res = super(IrUiView, self)._get_combined_arch()
        if self.model and self.env.user.last_view_model != self.model:
            self.env.user.sudo().last_view_model = self.model
        return res
