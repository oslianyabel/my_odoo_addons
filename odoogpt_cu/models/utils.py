import logging
import os
import re
import smtplib
from abc import ABC, abstractmethod
from datetime import datetime
from email.message import EmailMessage

import phonenumbers

from .enumerations import MessageType

_logger = logging.getLogger(__name__)
EMAIL = "julia.m@jumo.cat"
PASSWORD = "Esaiicvr1+1628"
HOST = "smtp.jumo.cat"
DEV_EMAIL = "o.abel@jumotech.com"
ADMIN_EMAIL = "oslianyabel@gmail.com"


def convert_dates(obj):
    if isinstance(obj, dict):
        return {k: convert_dates(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_dates(item) for item in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()

    return obj


def format_phone_number(phone_number: str) -> str | None:
    if not phone_number.startswith("+"):
        phone_number = f"+34 {phone_number}"

    try:
        parsed_phone = phonenumbers.parse(phone_number, None)
    except Exception:
        return None

    if parsed_phone and phonenumbers.is_valid_number(parsed_phone):
        formatted_phone_number = phonenumbers.format_number(
            parsed_phone, phonenumbers.PhoneNumberFormat.NATIONAL
        )
        return formatted_phone_number

    return None


def resume_chat(chat: list[dict], html_format: bool = True):
    _logger.debug("Resumiendo chat...")
    msg_base = """A continuación te paso una conversación entre un cliente y un asistente virtual. Necesito que resumas la conversación para que quede bien definida la intencion del cliente y se destaquen: el servicio que desea el cliente, los precios ofrecidos por el asistente, nombre del cliente y empresa a la que pertenece (si aparece)"""

    msg_html = msg_base + " Responde en formato html"
    msg_plain = (
        msg_base
        + " No utilices saltos de línea ni formato markdown, solo texto plano. Tu respuesta se enviará por email"
    )
    sys_msg = msg_html if html_format else msg_plain

    chat_str = ""
    for msg in chat:
        if "role" not in msg:
            continue

        if msg.get("role") not in [MessageType.USER.value, MessageType.ASSISTANT.value]:
            continue

        chat_str += f"{msg['role']}: {msg.get('content', '')} \n"

    # Importar localmente para evitar importación circular con completions
    from .completions import Agent

    resumidor = Agent(name="Resumidor", prompt=sys_msg)
    return resumidor.process_msg(chat_str, "resume_chat")


def send_email(EMAIL_TO, subject, message, pdf_path=None):
    _logger.info(f"Enviando correo a {EMAIL_TO} ...")

    email = EmailMessage()
    email["from"] = EMAIL
    email["to"] = EMAIL_TO
    email["subject"] = subject
    email.set_content(message)

    if pdf_path and os.path.isfile(pdf_path):
        with open(pdf_path, "rb") as pdf_file:
            pdf_data = pdf_file.read()
            email.add_attachment(
                pdf_data,
                maintype="application",
                subtype="pdf",
                filename=os.path.basename(pdf_path),
            )

    try:
        with smtplib.SMTP(HOST, port=587) as smtp:
            smtp.starttls()
            smtp.login(EMAIL, PASSWORD)
            smtp.sendmail(EMAIL, EMAIL_TO, email.as_string())

        _logger.info(f"Correo enviado! Destinatario: {EMAIL_TO}")
        return True

    except Exception as exc:
        _logger.error(f"Error enviando correo a {EMAIL_TO}: {exc}")
        return False


def notify_lead(partner, resume, client_email, lead):
    subject = "He creado un lead en el Odoo de Orion desde WhatsApp"
    message = "=" * 50
    message += f"\nNombre del usuario: {partner['name']}\n"
    message += f"Teléfono del usuario: {partner['phone']}\n"
    message += f"Email del usuario: {client_email}\n"
    message += f"ID del lead: {lead[0][0]}\n"
    message += f"Nombre del lead: {lead[0][1]}\n"
    message += f"Resumen de la conversación: \n{resume}"

    send_email(ADMIN_EMAIL, subject, message)
    send_email(DEV_EMAIL, subject, message)


def notify_sale_order(email, msg):
    send_email(
        EMAIL_TO=DEV_EMAIL,
        subject=f"Se ha creado un presupuesto para {email}",
        message=msg,
    )
    send_email(
        EMAIL_TO=ADMIN_EMAIL,
        subject=f"Se ha creado un presupuesto para {email}",
        message=msg,
    )
    send_email(
        EMAIL_TO=email,
        subject="Se ha creado un presupuesto para usted",
        message=msg,
    )


class Domain(ABC):
    @abstractmethod
    def get_domain(self):
        pass


class UserName(Domain):
    def __init__(self, name):
        self.name = name

    def get_domain(self):
        return [("name", "ilike", self.name)]


class UserEmail(Domain):
    def __init__(self, email):
        self.email = email

    def get_domain(self):
        return [("email", "=", self.email)]


class UserPhone(Domain):
    def __init__(self, phone: str):
        self.original_phone = phone
        if phone.startswith("+"):
            self.parsed_phone = self._parse_phone(phone)
        else:
            self.parsed_phone = self._parse_phone(f"+34 {phone}")

    def _parse_phone(self, phone):
        try:
            return phonenumbers.parse(phone, None)
        except Exception:
            return None

    def _is_valid_phone(self):
        return self.parsed_phone and phonenumbers.is_valid_number(self.parsed_phone)

    def get_domain(self):
        formats = []

        # Agregar el formato original
        formats.append(self.original_phone)

        if self._is_valid_phone():
            # Formato internacional completo con prefijo y sin espacios
            intl_format = phonenumbers.format_number(
                self.parsed_phone,  # type: ignore
                phonenumbers.PhoneNumberFormat.E164,  # type: ignore
            )
            formats.append(intl_format)

            # Formato internacional con espacios
            intl_spaced = phonenumbers.format_number(
                self.parsed_phone,  # type: ignore
                phonenumbers.PhoneNumberFormat.INTERNATIONAL,  # type: ignore
            )
            formats.append(intl_spaced)

            # Solo el número nacional (sin prefijo)
            national_format = phonenumbers.format_number(
                self.parsed_phone,  # type: ignore
                phonenumbers.PhoneNumberFormat.NATIONAL,  # type: ignore
            )
            formats.append(national_format)

            # Número nacional sin espacios ni caracteres especiales
            national_clean = re.sub(r"\D", "", national_format)
            formats.append(national_clean)

            # Variaciones con diferentes separadores
            formats.append(national_format.replace(" ", "-"))
            formats.append(national_format.replace(" ", "."))
            formats.append(national_format.replace(" ", ""))
        else:
            _logger.warning(
                f"El número de teléfono {self.original_phone} no es válido. No se generarán formatos adicionales."
            )

        # Eliminar duplicados y valores None/empty
        unique_formats = list(set([f for f in formats if f]))
        _logger.info(f"Phone formats: {unique_formats}")
        if not unique_formats:
            return []

        # Construir dominio con ORs: ['|', '|', ('phone','=','val1'), ('phone','=','val2'), ...]
        domain = []
        for i, phone_format in enumerate(unique_formats):
            if i > 0:
                domain.insert(0, "|")
            domain.append(("phone", "=", phone_format))
            domain.insert(0, "|")
            domain.append(("mobile", "=", phone_format))

        _logger.info(f"Domain: {domain}")
        return domain


class UserId(Domain):
    def __init__(self, id):
        self.id = id

    def get_domain(self):
        return [("id", "=", self.id)]
