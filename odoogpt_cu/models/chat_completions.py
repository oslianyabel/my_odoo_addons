import logging
from datetime import datetime, timedelta
from odoo import api, fields, models  # type: ignore
from .completions import Completions
from .prompt import JSON_TOOLS, SYS_MSG

_logger = logging.getLogger(__name__)


class ChatCompletions(models.Model):
    _name = "odoogpt.chat_completions"
    _description = "Agents Manager"
    _rec_name = "channel_id"

    # Class-level cache for completions
    _completions_cache = {}

    channel_id = fields.Many2one(
        "discuss.channel", string="Channel", required=True, ondelete="cascade"
    )
    last_activity = fields.Datetime(string="Last Activity", default=fields.Datetime.now)
    is_active = fields.Boolean(string="Is Active", default=True)

    _sql_constraints = [
        (
            "unique_channel",
            "unique(channel_id)",
            "Only one completion instance per channel is allowed.",
        )
    ]

    @api.model
    def get_or_create_completion(self, channel_id, tools_func):
        """Get or create a Completions instance for a specific channel"""
        # Search for existing record
        chat_completion = self.search([("channel_id", "=", channel_id.id)], limit=1)

        if not chat_completion:
            # Create new record
            chat_completion = self.create(
                {
                    "channel_id": channel_id.id,
                    "last_activity": fields.Datetime.now(),
                    "is_active": True,
                }
            )
            _logger.info(f"Created new Agent for channel {channel_id.id}")
        else:
            # Update last activity
            chat_completion.write(
                {"last_activity": fields.Datetime.now(), "is_active": True}
            )

        # Get or create Completions instance from cache
        cache_key = f"channel_{channel_id.id}"
        if cache_key not in self._completions_cache:
            self._completions_cache[cache_key] = Completions(
                name=f"Desoft Bot - Channel {channel_id.id}",
                json_tools=JSON_TOOLS,
                functions=tools_func,
                prompt=SYS_MSG,
            )
            _logger.info(
                f"Created new Completions instance for channel {channel_id.id}"
            )

        return self._completions_cache[cache_key]

    @api.model
    def cleanup_inactive_chats(self):
        """Clean up chat histories that have been inactive for more than 24 hours"""
        cutoff_time = datetime.now() - timedelta(hours=24)

        # Find inactive chat completions
        inactive_chats = self.search(
            [("last_activity", "<", cutoff_time), ("is_active", "=", True)]
        )

        cleaned_count = 0
        for chat in inactive_chats:
            try:
                # Remove from cache
                cache_key = f"channel_{chat.channel_id.id}"
                if cache_key in self._completions_cache:
                    del self._completions_cache[cache_key]

                # Mark as inactive
                chat.write({"is_active": False})
                cleaned_count += 1
                _logger.info(
                    f"Cleaned up inactive chat for channel {chat.channel_id.id}"
                )

            except Exception as e:
                _logger.error(f"Error cleaning up chat {chat.channel_id.id}: {str(e)}")

        _logger.info(f"Cleaned up {cleaned_count} inactive Agent")
        return cleaned_count

    @api.model
    def reset_chat_history(self, channel_id):
        """Reset the history for a specific chat"""
        cache_key = f"channel_{channel_id.id}"
        if cache_key in self._completions_cache:
            completion = self._completions_cache[cache_key]
            completion.reset_history()
            _logger.info(f"Reset history for channel {channel_id.id}")
            return True
        return False

    @api.model
    def _cron_cleanup_inactive_chats(self):
        """Cron job to automatically clean up inactive chats"""
        try:
            self.cleanup_inactive_chats()
        except Exception as e:
            _logger.error(f"Error in cron cleanup: {str(e)}")
