from homeassistant import config_entries
import voluptuous as vol
from .const import DOMAIN, CONF_AC_NAME, CONF_DEVICE_ID, CONF_DEVICE_LOCAL_KEY, CONF_DEVICE_IP, CONF_DEVICE_VERSION, CONF_DEVICE_MODEL, DEVICE_MODELS, DEVICE_VERSIONS, CONF_TEMPERATURE_SENSOR

class TuyaIrClimateConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Custom Climate entegrasyonu için config flow."""

    async def async_step_user(self, user_input=None):
        """İlk adımı yönet."""
        errors = {}
        if user_input is not None:
            # Kullanıcı girdilerini doğrula
            return self.async_create_entry(title=user_input[CONF_AC_NAME], data=user_input)

        data_schema = vol.Schema({
            vol.Required(CONF_AC_NAME): str,
            vol.Required(CONF_DEVICE_ID): str,
            vol.Required(CONF_DEVICE_LOCAL_KEY): str,
            vol.Required(CONF_DEVICE_IP): str,
            vol.Required(CONF_DEVICE_VERSION): vol.In(DEVICE_VERSIONS),
            vol.Required(CONF_DEVICE_MODEL): vol.In(DEVICE_MODELS),
            vol.Optional(CONF_TEMPERATURE_SENSOR, default=""): str,
        })

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    @staticmethod
    def async_get_options_flow(config_entry):
        return TuyaIrClimateOptionsFlow(config_entry)

class TuyaIrClimateOptionsFlow(config_entries.OptionsFlow):
    """Custom Climate entegrasyonu için seçenekler akışı."""

    def __init__(self, config_entry):
        """Seçenekler akışını başlat."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Seçenekleri yönet."""
        if user_input is not None:
            # Seçenekleri güncelle
            return self.async_create_entry(title="", data=user_input)

        data_schema = vol.Schema({
            vol.Optional(CONF_AC_NAME, default=self.config_entry.options.get(CONF_AC_NAME, self.config_entry.data.get(CONF_AC_NAME))): str,
            vol.Optional(CONF_DEVICE_ID, default=self.config_entry.options.get(CONF_DEVICE_ID, self.config_entry.data.get(CONF_DEVICE_ID))): str,
            vol.Optional(CONF_DEVICE_LOCAL_KEY, default=self.config_entry.options.get(CONF_DEVICE_LOCAL_KEY, self.config_entry.data.get(CONF_DEVICE_LOCAL_KEY))): str,
            vol.Optional(CONF_DEVICE_IP, default=self.config_entry.options.get(CONF_DEVICE_IP, self.config_entry.data.get(CONF_DEVICE_IP))): str,
            vol.Optional(CONF_DEVICE_VERSION, default=self.config_entry.options.get(CONF_DEVICE_VERSION, self.config_entry.data.get(CONF_DEVICE_VERSION))): vol.In(DEVICE_VERSIONS),
            vol.Optional(CONF_DEVICE_MODEL, default=self.config_entry.options.get(CONF_DEVICE_MODEL, self.config_entry.data.get(CONF_DEVICE_MODEL))): vol.In(DEVICE_MODELS),
            vol.Optional(CONF_TEMPERATURE_SENSOR, default=self.config_entry.options.get(CONF_TEMPERATURE_SENSOR, self.config_entry.data.get(CONF_TEMPERATURE_SENSOR, ""))): str,
        })

        return self.async_show_form(step_id="init", data_schema=data_schema)
