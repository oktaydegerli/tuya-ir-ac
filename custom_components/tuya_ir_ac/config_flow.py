from homeassistant import config_entries
import voluptuous as vol
from .const import DOMAIN, CONF_AC_NAME, CONF_DEVICE_ID, CONF_DEVICE_LOCAL_KEY, CONF_DEVICE_IP, CONF_DEVICE_VERSION, CONF_DEVICE_MODEL

class TuyaIrClimateConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Custom Climate entegrasyonu için config flow."""

    async def async_step_user(self, user_input=None):
        """İlk adımı yönet."""
        errors = {}
        if user_input is not None:
            # API anahtarını burada doğrulayabilirsiniz
            return self.async_create_entry(title="Custom Climate", data=user_input)

        data_schema = vol.Schema({
            vol.Required(CONF_AC_NAME): str,
            vol.Required(CONF_DEVICE_ID): str,
            vol.Required(CONF_DEVICE_LOCAL_KEY): str,
            vol.Required(CONF_DEVICE_IP): str,
            vol.Required(CONF_DEVICE_VERSION): str,
            vol.Required(CONF_DEVICE_MODEL): str
        })

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)