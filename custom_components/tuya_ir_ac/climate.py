from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (HVACMode, ClimateEntityFeature)
from homeassistant.const import (ATTR_TEMPERATURE, UnitOfTemperature)
from .const import DOMAIN, CONF_API_KEY

async def async_setup_entry(hass, config_entry, async_add_entities):
    api_key = hass.data[DOMAIN][config_entry.entry_id][CONF_API_KEY]
    async_add_entities([TuyaIrClimateEntity(api_key)])

class TuyaIrClimateEntity(ClimateEntity):
    def __init__(self, api_key):
        self._api_key = api_key
        self._attr_name = "Air Conditioner"
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_hvac_mode = HVACMode.OFF
        self._attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE | ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF
        self._attr_current_temperature = 20
        self._attr_target_temperature = 22

    @property
    def hvac_modes(self):
        return [HVACMode.OFF, HVACMode.COOL, HVACMode.FAN_ONLY, HVACMode.DRY, HVACMode.HEAT, HVACMode.HEAT_COOL]
    
    async def async_set_temperature(self, **kwargs):
        target_temperature = kwargs.get('temperature')
        if target_temperature is not None:
            self._attr_target_temperature = target_temperature
            # Burada API çağrısı yaparak gerçek cihaza komutu gönderebilirsiniz
            # Örneğin: await self._set_device_temperature(target_temperature)
            self.async_write_ha_state()
