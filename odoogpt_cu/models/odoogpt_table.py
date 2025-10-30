import os

from dotenv import load_dotenv
from deeplake.core.vectorstore import VectorStore
from odoo import api, fields, models, tools
from openai import OpenAI

os.environ["ACTIVELOOP_TOKEN"] = (
    "eyJhbGciOiJIUzUxMiIsImlhdCI6MTcwNjIxODE0MSwiZXhwIjoxNzM3ODQwNTI3fQ.eyJpZCI6ImpvamVkYSJ9.nONpytcgDe6RWuvD630V6ojhVoe8_rChvSF9Q7qbfz5Yobd_iaAhhiRZu4HiHK5KQ_s-e7EVw-60KKVJX0QuGQ"
)

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

IGNORE_TABLES = [
    "base",
    "_unknown",
    "ir_model",
    "ir_model_fields",
    "ir_model_fields_selection",
    "ir_model_constraint",
    "ir_model_relation",
    "ir_model_access",
    "ir_model_data",
    "ir_sequence",
    "ir_sequence_date_range",
    "ir_ui_menu",
    "ir_ui_view_custom",
    "ir_ui_view",
    "ir_asset",
    "ir_actions",
    "ir_act_window",
    "ir_act_window_view",
    "ir_act_url",
    "ir_act_server",
    "ir_server_object_lines",
    "ir_actions_todo",
    "ir_act_client",
    "ir_act_report_xml",
    "ir_attachment",
    "ir_binary",
    "ir_cron",
    "ir_cron_trigger",
    "ir_filters",
    "ir_default",
    "ir_exports",
    "ir_exports_line",
    "ir_rule",
    "ir_config_parameter",
    "ir_autovacuum",
    "ir_mail_server",
    "ir_fields_converter",
    "ir_qweb",
    "ir_qweb_field",
    "ir_qweb_field_integer",
    "ir_qweb_field_float",
    "ir_qweb_field_date",
    "ir_qweb_field_datetime",
    "ir_qweb_field_text",
    "ir_qweb_field_selection",
    "ir_qweb_field_many2one",
    "ir_qweb_field_many2many",
    "ir_qweb_field_html",
    "ir_qweb_field_image",
    "ir_qweb_field_image_url",
    "ir_qweb_field_monetary",
    "ir_qweb_field_float_time",
    "ir_qweb_field_time",
    "ir_qweb_field_duration",
    "ir_qweb_field_relative",
    "ir_qweb_field_barcode",
    "ir_qweb_field_contact",
    "ir_qweb_field_qweb",
    "ir_http",
    "ir_logging",
    "ir_property",
    "ir_module_category",
    "ir_module_module",
    "ir_module_module_dependency",
    "ir_module_module_exclusion",
    "report_layout",
    "report_paperformat",
    "ir_profile",
    "image_mixin",
    "avatar_mixin",
    "format_address_mixin",
    "res_currency_rate",
    "res_groups",
    "res_users_log",
    "res_users_apikeys",
    "res_users_apikeys_show",
    "res_users_deletion",
    "decimal_precision",
    "report_base_report_irmodulereference",
    "auth_totp_device",
    "base_import_mapping",
    "base_import_tests_models_char",
    "base_import_tests_models_char_required",
    "base_import_tests_models_char_readonly",
    "base_import_tests_models_char_states",
    "base_import_tests_models_char_noreadonly",
    "base_import_tests_models_char_stillreadonly",
    "base_import_tests_models_m2o",
    "base_import_tests_models_m2o_related",
    "base_import_tests_models_m2o_required",
    "base_import_tests_models_m2o_required_related",
    "base_import_tests_models_o2m",
    "base_import_tests_models_o2m_child",
    "base_import_tests_models_preview",
    "base_import_tests_models_float",
    "base_import_tests_models_complex",
    "bus_bus",
    "bus_presence",
    "ir_websocket",
    "resource_mixin",
    "resource_calendar",
    "resource_calendar_attendance",
    "resource_resource",
    "resource_calendar_leaves",
    "utm_campaign",
    "utm_medium",
    "utm_mixin",
    "utm_source",
    "utm_source_mixin",
    "utm_stage",
    "utm_tag",
    "web_tour_tour",
    "iap_account",
    "iap_enrich_api",
    "mail_alias",
    "mail_activity_mixin",
    "mail_alias_mixin",
    "mail_render_mixin",
    "mail_composer_mixin",
    "mail_thread",
    "mail_thread_blacklist",
    "mail_thread_cc",
    "template_reset_mixin",
    "fetchmail_server",
    "mail_notification",
    "mail_activity_type",
    "mail_activity",
    "mail_blacklist",
    "mail_followers",
    "mail_gateway_allowed",
    "mail_link_preview",
    "mail_message_reaction",
    "mail_message_schedule",
    "mail_message_subtype",
    "mail_message",
    "mail_mail",
    "mail_tracking_value",
    "mail_template",
    "mail_channel_member",
    "mail_channel_rtc_session",
    "mail_channel",
    "mail_guest",
    "mail_ice_server",
    "mail_shortcode",
    "res_users_settings",
    "res_users_settings_volumes",
    "publisher_warranty_contract",
    "web_editor_assets",
    "web_editor_converter_test",
    "web_editor_converter_test_sub",
    "google_gmail_mixin",
    "link_tracker",
    "link_tracker_code",
    "link_tracker_click",
    "mail_bot",
    "phone_blacklist",
    "mail_thread_phone",
    "privacy_log",
    "report_product_report_producttemplatelabel",
    "report_product_report_producttemplatelabel_dymo",
    "report_product_report_pricelist",
    "queue_job",
    "queue_job_channel",
    "queue_job_function",
    "rating_rating",
    "rating_mixin",
    "rating_parent_mixin",
    "spreadsheet_dashboard_group",
    "spreadsheet_dashboard",
    "iap_autocomplete_api",
    "res_partner_autocomplete_sync",
    "portal_mixin",
    "sms_api",
    "sms_sms",
    "sms_template",
    "snailmail_letter",
    "snailmail_confirm",
    "digest_digest",
    "digest_tip",
    "payment_provider",
    "payment_icon",
    "payment_token",
    "payment_transaction",
    "sequence_mixin",
    "report_account_report_invoice",
    "report_account_report_invoice_with_payments",
    "report_account_report_hash_integrity",
    "sale_report",
    "sale_order_option",
    "sale_order_template",
    "sale_order_template_line",
    "sale_order_template_option",
]


class OdooGPTTable(models.Model):
    _name = "odoogpt.table"
    _description = """Summary for tables uses in database. 
    If the table is not found, use the model description."""

    name = fields.Char(string="Table name", required=True)
    description = fields.Text(string="Table description", required=True, translate=True)

    def embedding_function(texts, model="text-embedding-3-small"):
        client = OpenAI(
            api_key=OPENAI_API_KEY
        )
        if isinstance(texts, str):
            texts = [texts]
        texts = [t.replace("\n", " ") for t in texts]
        return [
            data.embedding
            for data in client.embeddings.create(input=texts, model=model).data
        ]

    @api.model
    @tools.ormcache_context("self.env.registry.models", keys=("lang",))
    def _get_embeddings(self):
        """
        Obtains the tables in database and add it to a vector store
        :return: VectorStore: a vector store with the table_name and description as a document format
        """
        all_tables = {}
        for mod in self.env.registry.models.values():
            if not mod._transient and mod._table not in IGNORE_TABLES:
                all_tables[mod._table] = mod._description
        table_update = self.search([])
        for tab in table_update:
            all_tables[tab.name] = tab.description

        table_list = []
        for table_name, value in all_tables.items():
            try:
                table_list.append(
                    f'\{"table_name": {table_name}, "description": {value}\}'
                )
                # table_info = self._get_table_info(table_name)
                # all_tables[table_name] = {"description": all_tables[table_name], "data": table_info}
            except ValueError:
                continue

        vector_store = VectorStore()

        vector_store.add(
            text=table_list,
            embedding_function=self.embedding_function,
            embedding_data=table_list,
        )
        return vector_store

        # documents, metadatas, ids = [], [], []
        # for table_name, table_info in all_tables.items():
        #     documents.append(table_info)
        #     metadatas.append({'table_name': table_name})
        #     ids.append(table_name)

        # client = chromadb.Client()
        # collection = client.get_or_create_collection("odoo_tables_info")
        # collection.add(
        #         documents=documents,
        #         metadatas=metadatas,
        #         ids=ids
        # )
