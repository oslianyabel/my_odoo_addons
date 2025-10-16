import json
import logging
from datetime import timedelta

from odoo import fields  # type: ignore

from .utils import (
    Domain,
    UserEmail,
    UserId,
    UserName,
    UserPhone,
    convert_dates,
    format_phone_number,
    notify_lead,
    notify_sale_order,
    resume_chat,
)

_logger = logging.getLogger(__name__)


def send_odoo_msg(channel_id, odoogpt, message):
    channel_id.message_post(
        body=message,
        message_type="comment",
        author_id=odoogpt.id,
        email_from=odoogpt.email,
    )


def tool_create_sale_order_by_product_id(
    odoo_manager, odoogpt, channel_id, product_id, product_qty, email
) -> str:
    _logger.info("Creando pedido...")
    send_odoo_msg(
        channel_id,
        odoogpt,
        f"Estoy creando tu pedido con el producto ID {product_id} 📦",
    )

    partner = odoo_manager.get_partner_by_email(email)
    odoo_product = odoo_manager.get_product_by_id(product_id)

    if not partner:
        return f"No existe el usuario con email: {email}"

    if not odoo_product:
        return f"No existe producto con ID: {product_id}"

    return tool_create_sale_order(
        odoo_manager, odoo_product, product_qty, partner, email
    )


def tool_create_sale_order(
    odoo_manager,
    odoo_product,
    product_qty,
    partner,
    email,
):
    _logger.info("Creando sale_order...")
    product_qty = int(product_qty)
    if odoo_product["qty_available"] and odoo_product["qty_available"] < 1:
        return f"No hay stock disponible del producto {odoo_product['name']} en este momento"

    order_line = [
        {
            "product_id": odoo_product["id"],
            "product_uom_qty": product_qty,
            "price_unit": odoo_product["list_price"] * product_qty,
        },
    ]
    try:
        sale_order = odoo_manager.create_sale_order(partner["id"], order_line)
        sale_order_data = odoo_manager.get_sale_order_by_id(sale_order)
    except Exception as exc:
        _logger.error(f"Error creando sale_order: {exc}")
        return f"Ha ocurrido un error al intentar crear un pedido con el producto {odoo_product['name']}. Error: {exc}"

    msg = f"Nombre del producto: {odoo_product['name']}\nCantidad: {product_qty}\nMonto total: {odoo_product['list_price'] * product_qty}\nID del pedido: {sale_order}\nEnlace al presupuesto: {sale_order_data['link']}"

    notify_sale_order(email, msg)
    return f"Presupuesto creado! Número de seguimiento: {sale_order}"


def tool_create_lead(odoo_manager, odoogpt, channel_id, phone, name, email) -> str:
    _logger.info("Creando lead...")
    send_odoo_msg(
        channel_id,
        odoogpt,
        "Estoy analizando tu conversación para generar un nuevo lead 🧠",
    )

    phone = format_phone_number(phone)
    partner, status = odoo_manager.create_partner(name, phone, email)
    if status == "ERROR":
        return "Error durante la creación del partner"

    chat = odoo_manager._get_memory(odoogpt, channel_id)

    if not chat:
        msg = f"{phone} tiene el chat vacío"
        _logger.warning(msg)
        return msg

    resume_html = resume_chat(chat, html_format=True)
    resume_text = resume_chat(chat, html_format=False)

    lead = odoo_manager.create_lead(partner, resume_html, email)
    if not lead:
        return "Error al crear el lead. Por favor, verifica los datos del usuario"

    notify_lead(partner, resume_text, email, lead)
    return "Hemos registrado sus datos. Pronto nuestros comerciales se pondrán en contacto con usted"


def tool_get_partner_by_id(odoo_manager, odoogpt, channel_id, user_id) -> str:
    _logger.info(f"Buscando usuario con id {user_id}")
    send_odoo_msg(channel_id, odoogpt, f"Estoy buscando el usuario con id {user_id} 👤")
    partner = odoo_manager.get_partner_by_id(user_id)
    if not partner:
        return f"No existe ningún usuario con id {user_id}. Sugerir crear cuenta"
    elif len(partner) == 1:
        return f"Usuario encontrado: {partner}"

    return f"Usuarios encontrados: {partner}"


def tool_get_all_partners(odoo_manager, odoogpt, channel_id) -> str:
    _logger.info("🔍Consultando todos los clientes (partners)...")
    send_odoo_msg(channel_id, odoogpt, "Estoy buscando clientes 🔍")
    partners = odoo_manager.env["res.partner"].sudo().search([])
    fields = [
        "id",
        "name",
        "phone",
        "email",
        "function",  # Job position
        "street",  # Address street
        "street2",  # Address street 2
        "city",  # City
        "state_id",  # State
        "zip",  # Postal code
        "country_id",  # Country
        "is_company",  # Whether it's a company or individual
        "parent_id",
    ]
    data = partners.read(fields)
    return json.dumps(data)


def tool_create_partner(
    odoo_manager, odoogpt, channel_id, name, phone=None, email=None
) -> str:
    _logger.info("Creating partner...")
    send_odoo_msg(channel_id, odoogpt, f"Estoy creando tu usuario {name} 👤")
    partner, status = odoo_manager.create_partner(name, phone, email)
    if status == "ALREADY":
        return f"Ya existe al menos un usuario con ese teléfono o email en el sistema: {partner}"
    elif status == "CREATE":
        return f"Usuario creado: {partner}"

    return f"Error creando usuario. {status}"


def tool_get_sale_order_by_name(odoo_manager, odoogpt, channel_id, name) -> str:
    _logger.info(f"Buscando pedido con nombre {name}")
    send_odoo_msg(channel_id, odoogpt, f"Estoy buscando el pedido {name} 🔍")
    order = odoo_manager.get_sale_order_by_name(name)
    return json.dumps(convert_dates(order))


def tool_get_sale_order_by_id(odoo_manager, odoogpt, channel_id, id) -> str:
    _logger.info(f"Buscando pedido con id {id}")
    send_odoo_msg(channel_id, odoogpt, f"Estoy buscando el pedido con id {id} 🔍")
    order = odoo_manager.get_sale_order_by_id(id)
    return json.dumps(convert_dates(order))


def tool_get_all_products(odoo_manager, odoogpt, channel_id) -> str:
    _logger.info("🔍Consultando todos los productos...")
    send_odoo_msg(channel_id, odoogpt, "Estoy buscando productos 🔍")
    products = odoo_manager.get_all_products()
    if products:
        return json.dumps(products)

    return "Falló la consulta"


def tool_get_products_by_category_id(
    odoo_manager, category_id: int, odoogpt, channel_id
) -> str:
    _logger.info(f"Buscando productos por categoría id {category_id}")
    send_odoo_msg(
        channel_id,
        odoogpt,
        f"Estoy buscando productos de la categoría con id {category_id} 📂",
    )
    if isinstance(category_id, str):
        category_id = int(category_id)
    product = odoo_manager.get_products_by_category_id(category_id)
    if product:
        ans = json.dumps(product)
        return ans

    return f"No se encontraron productos con category_id {category_id}"


def tool_get_all_categories(odoo_manager, odoogpt, channel_id) -> str:
    _logger.info("Consultando categorías")
    send_odoo_msg(channel_id, odoogpt, "Estoy consultando categorías 🗃️")
    categories = odoo_manager.get_all_categories()
    if categories:
        return json.dumps(categories)

    return "Falló la obtención de categorías"


def orders_by_partner(
    odoo_manager,
    odoogpt,
    channel_id,
    domain: Domain,
):
    _logger.info(f"Consultando pedidos por domain: {domain}")
    partner = (
        odoo_manager.env["res.partner"].sudo().search(domain.get_domain(), limit=1)
    )
    if not partner:
        return "usuario no encontrado"

    if not partner["is_company"] and partner["parent_id"]:
        # Si el partner pertenece a una compañía tomar la compañía como referencia
        _logger.info(f"Partner pertenece a la compañía {partner['parent_id'][0]}")
        company = odoo_manager.get_partner_by_id(partner["parent_id"][0])
        sale_orders = odoo_manager.sale_orders_by_user_id(company["id"])
        if sale_orders:
            return json.dumps(convert_dates(sale_orders))

        _logger.info(f"La compañía {partner['parent_id'][0]} no tiene presupuestos")

    sale_orders = odoo_manager.sale_orders_by_user_id(partner["id"])
    if sale_orders:
        return json.dumps(convert_dates(sale_orders))

    msg = f"No se encontraron pedidos asociados al usuario: {partner['name']}"
    _logger.warning(msg)
    return msg


def orders_by_user_name(odoo_manager, odoogpt, channel_id, user_name):
    _logger.info(f"Consultando pedidos del usuario por nombre: {user_name}")
    send_odoo_msg(
        channel_id,
        odoogpt,
        f"Estoy consultando tus pedidos, {user_name} 🧾",
    )
    domain = UserName(user_name)
    return orders_by_partner(odoo_manager, odoogpt, channel_id, domain)


def orders_by_user_id(odoo_manager, odoogpt, channel_id, user_id):
    _logger.info(f"Consultando pedidos del usuario por id: {user_id}")
    send_odoo_msg(
        channel_id,
        odoogpt,
        f"Estoy consultando los pedidos del usuario con id {user_id} 🧾",
    )
    domain = UserId(user_id)
    return orders_by_partner(odoo_manager, odoogpt, channel_id, domain)


def orders_by_user_email(odoo_manager, odoogpt, channel_id, user_email):
    _logger.info(f"Consultando pedidos del usuario por email: {user_email}")
    send_odoo_msg(
        channel_id,
        odoogpt,
        f"Estoy consultando los pedidos del usuario {user_email} 🧾",
    )
    domain = UserEmail(user_email)
    return orders_by_partner(odoo_manager, odoogpt, channel_id, domain)


def orders_by_user_phone(odoo_manager, odoogpt, channel_id, user_phone):
    _logger.info(f"Consultando los pedidos del usuario {user_phone}")
    send_odoo_msg(
        channel_id,
        odoogpt,
        f"Estoy consultando los pedidos del usuario {user_phone} 🧾",
    )
    domain = UserPhone(user_phone)
    return orders_by_partner(odoo_manager, odoogpt, channel_id, domain)


def partners_with_pending_invoices_to_pay(odoo_manager, odoogpt, channel_id):
    _logger.info("Consultando clientes con facturas por cobrar")
    send_odoo_msg(
        channel_id, odoogpt, "Estoy consultando clientes con facturas por cobrar 💸"
    )
    query = """
        SELECT DISTINCT partner.id, partner.name
        FROM account_move invoice
        JOIN res_partner partner ON partner.id = invoice.partner_id
        WHERE invoice.payment_state != 'paid'
        AND invoice.state = 'posted'
    """
    odoo_manager.env.cr.execute(query)
    results = odoo_manager.env.cr.fetchall()

    if not results:
        return "No hay clientes con facturas por cobrar"

    count = len(results)
    names = [name for _, name in results]

    return f"Clientes con facturas por cobrar: {count}\n" + "\n".join(
        f"- {name}" for name in names
    )


def top_product_by_dates(odoo_manager, odoogpt, channel_id, start_date, end_date):
    _logger.info(f"Consultando producto más demandado entre {start_date} y {end_date}")
    send_odoo_msg(
        channel_id,
        odoogpt,
        f"Estoy consultando el producto más demandado desde {start_date} hasta {end_date} 🛒",
    )
    lines = (
        odoo_manager.env["sale.order.line"]
        .sudo()
        .read_group(
            [
                ("order_id.date_order", ">=", start_date),
                ("order_id.date_order", "<=", end_date),
            ],
            ["product_id", "product_uom_qty:sum"],
            ["product_id"],
        )
    )

    lines = sorted(lines, key=lambda x: x["product_uom_qty"], reverse=True)
    if not lines:
        return "No hay pedidos en el periodo"

    product = (
        odoo_manager.env["product.product"].sudo().browse(lines[0]["product_id"][0])
    )
    return f"Producto más demandado: {product.name} ({lines[0]['product_uom_qty']} unidades solicitadas desde {start_date} hasta {end_date})"


def pending_orders_to_send(odoo_manager, odoogpt, channel_id):
    _logger.info("Consultando pedidos pendientes de envío")
    send_odoo_msg(
        channel_id, odoogpt, "Estoy consultando pedidos pendientes de envío ⏳"
    )
    orders = (
        odoo_manager.env["sale.order"]
        .sudo()
        .search(
            [
                ("state", "in", ["sale", "done"]),
                ("picking_ids.state", "not in", ["done", "cancel"]),
            ]
        )
    )

    if not orders:
        return "Todos los pedidos están enviados"

    result_lines = []
    for order in orders:
        picking_states = ", ".join(set(p.state for p in order.picking_ids))
        product_lines = "\n".join(
            f"   - {line.product_id.name}: {line.product_uom_qty} unidades"
            for line in order.order_line
        )

        info = (
            f"📦 Pedido: {order.name}\n"
            f"👤 Cliente: {order.partner_id.name}\n"
            f"📅 Fecha: {order.date_order.strftime('%Y-%m-%d')}\n"
            f"💰 Total: ${order.amount_total:.2f}\n"
            f"🚚 Estado de envío: {picking_states or 'No definido'}\n"
            f"🛒 Productos:\n{product_lines}"
        )
        result_lines.append(info)

    return "\n\n".join(result_lines)


def canceled_orders_by_dates(odoo_manager, odoogpt, channel_id, start_date, end_date):
    _logger.info(f"Consultando pedidos cancelados entre {start_date} y {end_date}")
    send_odoo_msg(
        channel_id,
        odoogpt,
        f"Estoy consultando pedidos cancelados desde {start_date} hasta {end_date}...",
    )
    canceled_orders = (
        odoo_manager.env["sale.order"]
        .sudo()
        .search(
            [
                ("state", "=", "cancel"),
                ("date_order", ">=", start_date),
                ("date_order", "<=", end_date),
            ]
        )
    )

    if not canceled_orders:
        return "No hay pedidos cancelados este mes"

    info_lines = []
    for order in canceled_orders:
        info = (
            f"📦 {order.name} | Cliente: {order.partner_id.name} | "
            f"Fecha: {order.date_order.strftime('%Y-%m-%d')} | Total: ${order.amount_total:.2f}"
        )
        info_lines.append(info)

    return f"Pedidos cancelados este mes: {len(canceled_orders)}\n" + "\n".join(
        info_lines
    )


def product_stock(odoo_manager, odoogpt, channel_id, product_name):
    _logger.info(f"Consultando stock del producto: {product_name}")
    send_odoo_msg(
        channel_id,
        odoogpt,
        f"Estoy consultando el stock del producto {product_name} 📦",
    )
    product = (
        odoo_manager.env["product.product"]
        .sudo()
        .search([("name", "ilike", product_name)], limit=1)
    )

    if not product:
        return "Producto no encontrado"

    return f"Stock de {product.name}: {product.qty_available} unidades"


def paid_invoices_by_dates(odoo_manager, odoogpt, channel_id, start_date, end_date):
    _logger.info(f"Consultando facturas pagadas entre {start_date} y {end_date}")
    send_odoo_msg(
        channel_id,
        odoogpt,
        f"Estoy consultando facturas cobradas desde {start_date} hasta {end_date} 💰",
    )
    invoices = (
        odoo_manager.env["account.move"]
        .sudo()
        .search(
            [
                ("payment_state", "=", "paid"),
                ("invoice_date", ">=", start_date),
                ("invoice_date", "<=", end_date),
                ("move_type", "=", "out_invoice"),
            ]
        )
    )

    if not invoices:
        return "No hay facturas pagadas en el rango indicado"

    info_lines = []
    for inv in invoices:
        line = (
            f"🧾 Factura: {inv.name} | "
            f"Cliente: {inv.partner_id.name} | "
            f"Fecha: {inv.invoice_date} | "
            f"Total: ${inv.amount_total:.2f}"
        )
        info_lines.append(line)

    total = sum(inv.amount_total for inv in invoices)
    return (
        f"Facturas pagadas: {len(invoices)}\n"
        f"Total recaudado: ${total:.2f}\n\n" + "\n".join(info_lines)
    )


def partners_paid_invoices_by_dates(
    odoo_manager, odoogpt, channel_id, start_date, end_date
):
    _logger.info(
        f"Obteniendo importe acumulado de facturas pagadas entre {start_date} y {end_date}"
    )
    send_odoo_msg(
        channel_id,
        odoogpt,
        f"Estoy obteniendo el importe acumulado en facturas pagadas por cada cliente entre {start_date} y {end_date} 💰",
    )

    query = """
        SELECT partner.name, COUNT(*) AS count
        FROM account_move
        JOIN res_partner partner ON partner.id = account_move.partner_id
        WHERE account_move.payment_state = 'paid'
          AND account_move.state = 'posted'
          AND account_move.move_type = 'out_invoice'
          AND account_move.invoice_date BETWEEN %s AND %s
        GROUP BY partner.name
        ORDER BY count DESC
    """
    odoo_manager.env.cr.execute(query, (start_date, end_date))
    results = odoo_manager.env.cr.fetchall()

    if not results:
        return "No se encontraron facturas pagadas en ese rango de fechas"

    # Mostrar hasta 50 resultados o resumen
    if len(results) > 50:
        avg = sum(row[1] for row in results) / len(results)
        return (
            f"{len(results)} clientes - Promedio de facturas pagadas: {round(avg, 2)}"
        )

    return "\n".join([f"{name}: {count} facturas pagadas" for name, count in results])


def products_highest_margin(odoo_manager, odoogpt, channel_id):
    _logger.info("Consultando productos con mayor margen")
    send_odoo_msg(
        channel_id, odoogpt, "Estoy consultando productos con mayor margen-beneficio 📊"
    )
    products = (
        odoo_manager.env["product.product"].sudo().search([("standard_price", ">", 0)])
    )

    products_with_margin = sorted(
        products, key=lambda p: p.list_price - p.standard_price, reverse=True
    )

    top_products = products_with_margin[:10]

    return (
        "\n".join(
            [
                f"{p.name}: Margen ${round(p.list_price - p.standard_price, 2)} "
                f"({round((p.list_price - p.standard_price) / p.standard_price * 100, 2)}%)"
                for p in top_products
            ]
        )
        or "No hay datos de margen"
    )


def orders_by_product_id(odoo_manager, odoogpt, channel_id, product_id: int) -> str:
    send_odoo_msg(
        channel_id,
        odoogpt,
        f"Estoy consultando pedidos del producto con id {product_id} 🛒",
    )
    _logger.info(f"Consultando pedidos del producto con ID {product_id}")
    try:
        product_id = int(product_id)
        product = odoo_manager.env["product.product"].sudo().browse(product_id)
        if not product.exists():
            return f"No se encontró el producto con ID {product_id}"

        lines = (
            odoo_manager.env["sale.order.line"]
            .sudo()
            .search([("product_id", "=", product_id)])
        )

        if not lines:
            return f"No se encontraron pedidos asociados al producto '{product.name}'"

        total_qty = sum(line.product_uom_qty for line in lines)
        total_orders = sum(line.price_subtotal for line in lines)

        # Agrupar por pedido
        orders_info = []
        for line in lines:
            order = line.order_id
            orders_info.append(
                f"📦 Pedido: {order.name}\n"
                f"👤 Cliente: {order.partner_id.name}\n"
                f"📅 Fecha: {order.date_order.strftime('%Y-%m-%d')}\n"
                f"💰 Total del pedido: ${order.amount_total:.2f}\n"
                f"📌 Estado: {order.state}\n"
                f"🛒 Producto: {line.product_id.name} - {line.product_uom_qty} unidades - Subtotal: ${line.price_subtotal:.2f}\n"
                f"{'-' * 40}"
            )

        return (
            f"🛒Pedidos del producto '{product.name}':\n"
            f"- Total de unidades solicitadas: {total_qty}\n"
            f"- Monto total acumulado: ${total_orders:.2f}\n\n" + "\n".join(orders_info)
        )
    except Exception as e:
        _logger.error(f"Error consultando pedidos del producto {product_id}: {e}")
        return "Ocurrió un error al intentar consultar las pedidos del producto"


def top_partner_by_invoices_count(odoo_manager, odoogpt, channel_id, start_date):
    _logger.info(f"Buscando cliente con más facturas pagadas desde {start_date}")
    send_odoo_msg(
        channel_id,
        odoogpt,
        "Estoy buscando al cliente con mayor cantidad de facturas pagadas 👤",
    )
    query = """
        SELECT partner.name, COUNT(*) AS count
        FROM account_move
        JOIN res_partner partner ON partner.id = account_move.partner_id
        WHERE account_move.payment_state = 'paid'
          AND account_move.state = 'posted'
          AND account_move.move_type = 'out_invoice'
          AND account_move.invoice_date >= %s
        GROUP BY partner.name
        ORDER BY count DESC
        LIMIT 1
    """
    odoo_manager.env.cr.execute(query, (start_date,))
    result = odoo_manager.env.cr.dictfetchone()

    if result:
        return f"🏆Cliente con más facturas pagadas desde {start_date}: {result['name']} ({result['count']} facturas)"

    return f"No se encontraron facturas pagadas a partir de {start_date}"


def top_partner_by_payments_volume(
    odoo_manager, odoogpt, channel_id, start_date
) -> str:
    _logger.info(f"Buscando cliente con mayor volumen de ingresos desde {start_date}")
    send_odoo_msg(
        channel_id,
        odoogpt,
        "Estoy buscando al cliente con mayor volumen de ingresos 👤",
    )
    query = """
        SELECT partner.name, SUM(account_move.amount_total) AS total
        FROM account_move
        JOIN res_partner partner ON partner.id = account_move.partner_id
        WHERE account_move.payment_state = 'paid'
          AND account_move.state = 'posted'
          AND account_move.move_type = 'out_invoice'
          AND account_move.invoice_date >= %s
        GROUP BY partner.name
        ORDER BY total DESC
        LIMIT 1
    """
    odoo_manager.env.cr.execute(query, (start_date,))
    result = odoo_manager.env.cr.dictfetchone()

    if result:
        return f"💰Cliente con mayor facturación desde {start_date}: {result['name']} (${result['total']:.2f})"

    return f"No se encontraron facturas pagadas a partir de {start_date}"


def orders_by_dates(odoo_manager, odoogpt, channel_id, start_date, end_date):
    _logger.info(f"Buscando pedidos entre {start_date} y {end_date}")
    send_odoo_msg(
        channel_id,
        odoogpt,
        f"Estoy buscando pedidos solicitados desde {start_date} hasta {end_date} 📦",
    )
    orders = (
        odoo_manager.env["sale.order"]
        .sudo()
        .search([("date_order", ">=", start_date), ("date_order", "<=", end_date)])
    )
    return (
        "\n".join(
            [
                f"{order.name}: {order.partner_id.name} - ${order.amount_total}"
                for order in orders
            ]
        )
        or "No hay pedidos"
    )


def pending_invoices_to_pay_by_dates(
    odoo_manager, odoogpt, channel_id, start_date, end_date
):
    _logger.info(f"Consultando facturas por cobrar entre {start_date} y {end_date}")
    send_odoo_msg(
        channel_id,
        odoogpt,
        f"Estoy consultando facturas por cobrar desde {start_date} hasta {end_date} 💰",
    )
    invoices = (
        odoo_manager.env["account.move"]
        .sudo()
        .search(
            [
                ("payment_state", "!=", "paid"),
                ("invoice_date", ">=", start_date),
                ("invoice_date", "<=", end_date),
                ("state", "=", "posted"),
                ("move_type", "=", "out_invoice"),
            ]
        )
    )

    if not invoices:
        return "No hay facturas por cobrar"

    lines = []
    for inv in invoices:
        lines.append(
            f"🧾 Factura: {inv.name} | "
            f"Cliente: {inv.partner_id.name} | "
            f"Fecha: {inv.invoice_date} | "
            f"Total: ${inv.amount_total:.2f} | "
            f"Estado: {inv.payment_state}"
        )

    total = sum(inv.amount_total for inv in invoices)
    return (
        f"Facturas pendientes: {len(invoices)}\n"
        f"Monto total pendiente: ${total:.2f}\n\n" + "\n".join(lines)
    )


def products_low_stock(odoo_manager, odoogpt, channel_id):
    _logger.info("Consultando productos con bajo stock")
    send_odoo_msg(channel_id, odoogpt, "Estoy consultando productos con bajo stock 📦")
    products = (
        odoo_manager.env["product.product"]
        .sudo()
        .search([("qty_available", "<", 10), ("type", "=", "product")])
    )
    return (
        "\n".join(
            [
                f"{product.name}: {product.qty_available} unidades"
                for product in products
            ]
        )
        or "Todo el stock está OK"
    )


def products_qty_by_dates(odoo_manager, odoogpt, channel_id, start_date, end_date):
    _logger.info(f"Consultando demanda por producto entre {start_date} y {end_date}")
    send_odoo_msg(
        channel_id,
        odoogpt,
        f"Estoy consultando la demanda por producto desde {start_date} hasta {end_date} 🛒",
    )
    lines = (
        odoo_manager.env["sale.order.line"]
        .sudo()
        .read_group(
            [
                ("order_id.date_order", ">=", start_date),
                ("order_id.date_order", "<=", end_date),
            ],
            ["product_id", "price_subtotal", "product_uom_qty:sum"],
            ["product_id"],
        )
    )

    if len(lines) > 50:
        avg = sum(line["price_subtotal"] for line in lines) / len(lines)
        return f"Promedio por producto: ${round(avg, 2)}"

    return "\n".join(
        [
            f"{odoo_manager.env['product.product'].sudo().browse(line['product_id'][0]).name}: "
            f"{line['product_uom_qty']} unidades, ${line['price_subtotal']}"
            for line in lines
        ]
    )


def recent_leads(odoo_manager, odoogpt, channel_id):
    _logger.info("Consultando leads recientes")
    send_odoo_msg(channel_id, odoogpt, "Estoy consultando leads recientes 🧠")
    leads = (
        odoo_manager.env["crm.lead"]
        .sudo()
        .search(
            [("create_date", ">=", fields.Datetime.now() - timedelta(days=7))], limit=10
        )
    )

    return (
        "\n".join(
            [
                f"{lead.name}: {lead.partner_name or 'N/A'} - {lead.stage_id.name}"
                for lead in leads
            ]
        )
        or "No hay leads recientes"
    )


# ======= CALENDAR EVENT FUNCTIONS =======


def tool_create_calendar_event(
    odoo_manager,
    odoogpt,
    channel_id,
    name,
    start_datetime,
    end_datetime=None,
    description=None,
    partner_ids=None,
    location=None,
    allday=False,
    duration=1.0,
):
    """Crear un evento de calendario"""
    _logger.info(f"Creando evento de calendario: {name}")
    send_odoo_msg(channel_id, odoogpt, f"Estoy creando el evento '{name}' 📅")

    try:
        result = odoo_manager.create_calendar_event(
            name=name,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            description=description,
            partner_ids=partner_ids,
            location=location,
            allday=allday,
            duration=duration,
        )

        if result.get("status") == "created":
            # Respuesta más concisa para evitar truncamiento
            start_date = result.get("start", "").split(" ")[0]  # Solo la fecha
            start_time = (
                result.get("start", "").split(" ")[1]
                if " " in result.get("start", "")
                else ""
            )  # Solo la hora

            return f"✅ Evento creado: {result['name']}\n📅 {start_date} a las {start_time}\n🎯 ID: {result['id']}"
        else:
            return f"❌ {result.get('message', 'Error al crear el evento')}"

    except Exception as e:
        _logger.error(f"Error en tool_create_calendar_event: {str(e)}")
        return f"❌ Error al crear el evento: {str(e)}"


def tool_get_calendar_events(
    odoo_manager,
    odoogpt,
    channel_id,
    start_date=None,
    end_date=None,
    partner_id=None,
    search_term=None,
    limit=20,
):
    """Consultar eventos de calendario"""
    _logger.info("Consultando eventos de calendario")
    send_odoo_msg(channel_id, odoogpt, "Estoy consultando los eventos de calendario 📅")

    try:
        # Si partner_id es 0, no filtrar por partner
        filter_partner_id = partner_id if partner_id and partner_id > 0 else None

        events = odoo_manager.get_calendar_events(
            start_date=start_date,
            end_date=end_date,
            partner_id=filter_partner_id,
            search_term=search_term,
            limit=limit,
        )

        if not events:
            return "📅 No se encontraron eventos con los criterios especificados"

        result_lines = [f"📅 Encontrados {len(events)} eventos:"]
        for event in events:
            attendees_info = (
                f" (👥 {len(event['attendees'])} asistentes)"
                if event["attendees"]
                else ""
            )
            location_info = f" 📍 {event['location']}" if event["location"] else ""

            result_lines.append(
                f"• {event['name']}\n"
                f"  🕐 {event['start']} - {event['stop']}{attendees_info}{location_info}"
            )

        return "\n".join(result_lines)

    except Exception as e:
        _logger.error(f"Error en tool_get_calendar_events: {str(e)}")
        return f"❌ Error al consultar eventos: {str(e)}"


def tool_get_upcoming_events(odoo_manager, odoogpt, channel_id, days_ahead=7, limit=10):
    """Obtener eventos próximos"""
    _logger.info("Consultando eventos próximos")
    send_odoo_msg(channel_id, odoogpt, "Estoy consultando tus eventos próximos 🔮")

    try:
        events = odoo_manager.get_upcoming_events(days_ahead=days_ahead, limit=limit)

        if not events:
            return f"📅 No tienes eventos programados en los próximos {days_ahead} días"

        result_lines = [f"🔮 Próximos eventos ({len(events)}):"]
        for event in events:
            attendees_str = ", ".join(event["attendees"][:2])
            if len(event["attendees"]) > 2:
                attendees_str += f" y {len(event['attendees']) - 2} más"
            attendees_info = f" 👥 {attendees_str}" if attendees_str else ""

            result_lines.append(
                f"• {event['name']}\n"
                f"  ⏰ {event['time_remaining']} - {event['start']}{attendees_info}"
            )

        return "\n".join(result_lines)

    except Exception as e:
        _logger.error(f"Error en tool_get_upcoming_events: {str(e)}")
        return f"❌ Error al consultar eventos próximos: {str(e)}"


def tool_update_calendar_event(odoo_manager, odoogpt, channel_id, event_id, **kwargs):
    """Actualizar un evento de calendario"""
    _logger.info(f"Actualizando evento de calendario ID: {event_id}")
    send_odoo_msg(channel_id, odoogpt, "Estoy actualizando el evento 📝")

    try:
        result = odoo_manager.update_calendar_event(event_id, **kwargs)

        if result.get("status") == "success":
            return f"✅ {result['message']}"
        else:
            return f"❌ {result.get('message', 'Error al actualizar el evento')}"

    except Exception as e:
        _logger.error(f"Error en tool_update_calendar_event: {str(e)}")
        return f"❌ Error al actualizar el evento: {str(e)}"


def tool_delete_calendar_event(odoo_manager, odoogpt, channel_id, event_id):
    """Eliminar un evento de calendario"""
    _logger.info(f"Eliminando evento de calendario ID: {event_id}")
    send_odoo_msg(channel_id, odoogpt, "Estoy eliminando el evento 🗑️")

    try:
        result = odoo_manager.delete_calendar_event(event_id)

        if result.get("status") == "success":
            return f"✅ {result['message']}"
        else:
            return f"❌ {result.get('message', 'Error al eliminar el evento')}"

    except Exception as e:
        _logger.error(f"Error en tool_delete_calendar_event: {str(e)}")
        return f"❌ Error al eliminar el evento: {str(e)}"


# ======= SURVEY FUNCTIONS =======


def tool_get_all_surveys(odoo_manager, odoogpt, channel_id, limit=100, state=None):
    """Obtener lista de todas las encuestas disponibles"""
    _logger.info("Consultando todas las encuestas")
    send_odoo_msg(channel_id, odoogpt, "Estoy consultando las encuestas disponibles 📊")

    try:
        domain = []
        # Usar 'active' en lugar de 'state' ya que survey.survey no tiene campo 'state'
        if state == "active":
            domain.append(("active", "=", True))
        elif state == "inactive":
            domain.append(("active", "=", False))

        surveys = (
            odoo_manager.env["survey.survey"]
            .sudo()
            .search(domain, limit=limit, order="create_date desc")
        )

        if not surveys:
            return "📊 No se encontraron encuestas"

        result_lines = [f"📊 Encontradas {len(surveys)} encuestas:"]
        for survey in surveys:
            active_emoji = "🟢" if survey.active else "🔴"
            survey_type_emoji = {
                "survey": "📋",
                "live_session": "🎯",
                "assessment": "📝",
                "custom": "⚙️",
            }.get(survey.survey_type, "❓")

            result_lines.append(
                f"• {active_emoji} {survey_type_emoji} {survey.title} (ID: {survey.id})\n"
                f"  📅 Creada: {survey.create_date.strftime('%Y-%m-%d')}\n"
                f"  📊 Tipo: {survey.survey_type}\n"
                f"  ✅ Activa: {'Sí' if survey.active else 'No'}\n"
                f"  📈 Respuestas: {survey.answer_count}"
            )

        return "\n".join(result_lines)

    except Exception as e:
        _logger.error(f"Error en tool_get_all_surveys: {str(e)}")
        return f"❌ Error al consultar encuestas: {str(e)}"


def tool_get_survey_results(
    odoo_manager, odoogpt, channel_id, survey_id, include_answers=False
):
    """Obtener estadísticas y resultados completos de una encuesta específica"""
    _logger.info(f"Consultando resultados de encuesta ID: {survey_id}")
    send_odoo_msg(
        channel_id, odoogpt, "Estoy analizando los resultados de la encuesta 📊"
    )

    try:
        survey = odoo_manager.env["survey.survey"].sudo().browse(survey_id)
        if not survey.exists():
            return f"❌ No se encontró la encuesta con ID {survey_id}"

        # Obtener todas las respuestas para estadísticas
        all_user_inputs = (
            odoo_manager.env["survey.user_input"]
            .sudo()
            .search([("survey_id", "=", survey_id)])
        )

        # Calcular estadísticas generales
        total_responses = len(all_user_inputs)
        completed_responses = len(all_user_inputs.filtered(lambda x: x.state == "done"))
        in_progress_responses = len(
            all_user_inputs.filtered(lambda x: x.state == "in_progress")
        )
        completion_rate = (
            (completed_responses / total_responses * 100) if total_responses > 0 else 0
        )

        # Construir resultado con estadísticas
        result = f"📊 Resultados de '{survey.title}':\n\n"
        result += "📈 ESTADÍSTICAS GENERALES:\n"
        result += f"🎯 Total de respuestas: {total_responses}\n"
        result += f"✅ Completadas: {completed_responses}\n"
        result += f"⏳ En progreso: {in_progress_responses}\n"
        result += f"📈 Tasa de finalización: {completion_rate:.1f}%\n"
        result += f"📊 Tipo: {survey.survey_type}\n"
        result += f"✅ Activa: {'Sí' if survey.active else 'No'}\n"
        result += f"⭐ Puntuación promedio: {survey.answer_score_avg:.1f}%\n"
        result += f"⏱️ Duración promedio: {survey.answer_duration_avg:.1f}h\n\n"

        # Si no hay respuestas completadas, terminar aquí
        completed_user_inputs = all_user_inputs.filtered(lambda x: x.state == "done")
        if not completed_user_inputs:
            result += "📊 No hay respuestas completadas para mostrar detalles."
            return result

        # Si se solicitan respuestas detalladas
        if include_answers:
            result += "📋 RESPUESTAS DETALLADAS POR USUARIO:\n\n"

            # Obtener preguntas de la encuesta para referencia
            questions = (
                odoo_manager.env["survey.question"]
                .sudo()
                .search([("survey_id", "=", survey_id)], order="sequence")
            )

            result += f"❓ Total de preguntas: {len(questions)}\n"
            result += f"👥 Usuarios que completaron: {len(completed_user_inputs)}\n\n"

            # Iterar por cada usuario que completó la encuesta
            for user_input in completed_user_inputs:
                # Nombre del usuario
                user_name = (
                    user_input.partner_id.name
                    if user_input.partner_id
                    else user_input.email or "Usuario Anónimo"
                )

                result += f"👤 {user_name}\n"
                result += f"   📅 Completado: {user_input.end_datetime.strftime('%Y-%m-%d %H:%M') if user_input.end_datetime else 'N/A'}\n"

                # Obtener todas las respuestas de este usuario
                user_answers = (
                    odoo_manager.env["survey.user_input.line"]
                    .sudo()
                    .search(
                        [("user_input_id", "=", user_input.id)],
                        order="question_sequence",
                    )
                )

                if user_answers:
                    result += f"   📝 Respuestas ({len(user_answers)}):\n"

                    for answer in user_answers:
                        # Obtener el título de la pregunta
                        question_title = (
                            answer.question_id.title or "Pregunta sin título"
                        )

                        # Obtener el valor de la respuesta según su tipo
                        answer_value = ""
                        if answer.answer_type == "char_box" and answer.value_char_box:
                            answer_value = answer.value_char_box
                        elif answer.answer_type == "text_box" and answer.value_text_box:
                            answer_value = answer.value_text_box
                        elif (
                            answer.answer_type == "numerical_box"
                            and answer.value_numerical_box
                        ):
                            answer_value = str(answer.value_numerical_box)
                        elif answer.answer_type == "date" and answer.value_date:
                            answer_value = str(answer.value_date)
                        elif answer.answer_type == "datetime" and answer.value_datetime:
                            answer_value = str(answer.value_datetime)
                        elif (
                            answer.answer_type == "suggestion"
                            and answer.suggested_answer_id
                        ):
                            answer_value = answer.suggested_answer_id.value

                        if answer_value:
                            result += f"     ❓ {question_title}\n"
                            result += f"     ✅ {answer_value}\n\n"
                        else:
                            result += f"     ❓ {question_title}\n"
                            result += "     ❌ [Sin respuesta]\n\n"
                else:
                    result += "   📝 Sin respuestas registradas\n"

                result += "\n" + "=" * 50 + "\n\n"

        return result

    except Exception as e:
        _logger.error(f"Error en tool_get_survey_results: {str(e)}")
        return f"❌ Error al obtener resultados: {str(e)}"


tools_func = {
    # leads
    # "create_lead": tool_create_lead,
    "recent_leads": recent_leads,
    # calendar events
    "create_calendar_event": tool_create_calendar_event,
    "get_calendar_events": tool_get_calendar_events,
    "get_upcoming_events": tool_get_upcoming_events,
    "update_calendar_event": tool_update_calendar_event,
    "delete_calendar_event": tool_delete_calendar_event,
    # survey tools
    "get_all_surveys": tool_get_all_surveys,
    "get_survey_results": tool_get_survey_results,
    # partners
    "create_partner": tool_create_partner,
    "tool_get_partner_by_id": tool_get_partner_by_id,
    "get_all_partners": tool_get_all_partners,
    "partners_with_pending_invoices_to_pay": partners_with_pending_invoices_to_pay,
    "top_partner_by_invoices_count": top_partner_by_invoices_count,
    "top_partner_by_payments_volume": top_partner_by_payments_volume,
    "partners_paid_invoices_by_dates": partners_paid_invoices_by_dates,
    # sale orders
    "create_sale_order_by_product_id": tool_create_sale_order_by_product_id,
    "get_sale_order_by_name": tool_get_sale_order_by_name,
    "get_sale_order_by_id": tool_get_sale_order_by_id,
    "orders_by_dates": orders_by_dates,
    "canceled_orders_by_dates": canceled_orders_by_dates,
    "orders_by_user_name": orders_by_user_name,
    "orders_by_user_id": orders_by_user_id,
    "orders_by_user_email": orders_by_user_email,
    "orders_by_user_phone": orders_by_user_phone,
    "orders_by_product_id": orders_by_product_id,
    "pending_orders_to_send": pending_orders_to_send,
    # products
    "get_all_products": tool_get_all_products,
    "get_products_by_category_id": tool_get_products_by_category_id,
    "get_all_categories": tool_get_all_categories,
    "products_low_stock": products_low_stock,
    "top_product_by_dates": top_product_by_dates,
    "products_qty_by_dates": products_qty_by_dates,
    "products_highest_margin": products_highest_margin,
    # invoices
    "paid_invoices_by_dates": paid_invoices_by_dates,
    "pending_invoices_to_pay_by_dates": pending_invoices_to_pay_by_dates,
}
