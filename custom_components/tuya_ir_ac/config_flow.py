from homeassistant import config_entries
from .const import DOMAIN

class TuyaIrClimateConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="Air Conditioner", data=user_input)

        return self.async_show_form(step_id="user")
