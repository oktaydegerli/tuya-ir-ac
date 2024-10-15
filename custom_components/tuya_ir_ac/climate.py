from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    HVAC_MODE_HEAT,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import TEMP_CELSIUS

async def async_setup_entry(hass, config_entry, async_add_entities):
    async_add_entities([TuyaIrClimateEntity()])

class TuyaIrClimateEntity(ClimateEntity):
    def __init__(self):
        self._attr_name = "Air Conditioner"
        self._attr_temperature_unit = TEMP_CELSIUS
        self._attr_hvac_mode = HVAC_MODE_HEAT
        self._attr_supported_features = SUPPORT_TARGET_TEMPERATURE
        self._attr_current_temperature = 20
        self._attr_target_temperature = 22

    @property
    def hvac_modes(self):
        return [HVAC_MODE_HEAT]
