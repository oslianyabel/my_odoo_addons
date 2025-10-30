from odoo import api, fields, models  # type: ignore


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    desoft_tools_partners = fields.Boolean(string="Habilitar herramientas de Clientes", default=True, config_parameter='odoogpt.tools.partners')
    desoft_tools_products = fields.Boolean(string="Habilitar herramientas de Productos", default=True, config_parameter='odoogpt.tools.products')
    desoft_tools_orders = fields.Boolean(string="Habilitar herramientas de Pedidos", default=True, config_parameter='odoogpt.tools.orders')
    desoft_tools_invoices = fields.Boolean(string="Habilitar herramientas de Facturas", default=True, config_parameter='odoogpt.tools.invoices')
    desoft_tools_leads = fields.Boolean(string="Habilitar herramientas de Leads", default=True, config_parameter='odoogpt.tools.leads')
