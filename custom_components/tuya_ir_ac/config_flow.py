from homeassistant import config_entries
import voluptuous as vol
from .const import DOMAIN, CONF_API_KEY

class TuyaIrClimateConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Custom Climate entegrasyonu için config flow."""

    async def async_step_user(self, user_input=None):
        """İlk adımı yönet."""
        errors = {}
        if user_input is not None:
            # API anahtarını burada doğrulayabilirsiniz
            return self.async_create_entry(title="Custom Climate", data=user_input)

        data_schema = vol.Schema({
            vol.Required(CONF_API_KEY): str
        })

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)