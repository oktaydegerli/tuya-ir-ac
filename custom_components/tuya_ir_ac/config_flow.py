import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN, CONF_API_KEY, CONF_NAME # const.py dosyanızdan import edin

_LOGGER = logging.getLogger(__name__)

class TuyaIrClimateConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Örnek Klima için konfigürasyon akışı."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Kullanıcı arayüzündeki konfigürasyon adımı."""
        errors = {}

        if user_input is not None:
            # Gerekli doğrulamaları burada yapın (örneğin, API anahtarının geçerliliği)

            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME): str,
                    vol.Required(CONF_API_KEY): str,
                }
            ),
            errors=errors,
        )