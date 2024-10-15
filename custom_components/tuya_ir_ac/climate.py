from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (HVACMode, ClimateEntityFeature)
from homeassistant.const import (ATTR_TEMPERATURE, UnitOfTemperature)
from .const import DOMAIN, CONF_AC_NAME, CONF_DEVICE_ID, CONF_DEVICE_LOCAL_KEY, CONF_DEVICE_IP, CONF_DEVICE_VERSION, CONF_DEVICE_MODEL

async def async_setup_entry(hass, config_entry, async_add_entities):
    ac_name = hass.data[DOMAIN][config_entry.entry_id][CONF_AC_NAME]
    device_id = hass.data[DOMAIN][config_entry.entry_id][CONF_DEVICE_ID]
    device_local_key = hass.data[DOMAIN][config_entry.entry_id][CONF_DEVICE_LOCAL_KEY]
    device_ip = hass.data[DOMAIN][config_entry.entry_id][CONF_DEVICE_IP]
    device_version = hass.data[DOMAIN][config_entry.entry_id][CONF_DEVICE_VERSION]
    device_model = hass.data[DOMAIN][config_entry.entry_id][CONF_DEVICE_MODEL]
    async_add_entities([TuyaIrClimateEntity(ac_name, device_id, device_local_key, device_ip, device_version, device_model)])

class TuyaIrClimateEntity(ClimateEntity):
    def __init__(self, ac_name, device_id, device_local_key, device_ip, device_version, device_model):
        self._enable_turn_on_off_backwards_compatibility = False
        self._ac_name = ac_name
        self._device_id = device_id
        self._device_local_key = device_local_key
        self._device_ip = device_ip
        self._device_version = device_version
        self._device_model = device_model
        self._attr_is_on = False
        self._attr_hvac_mode = HVACMode.OFF
        self._attr_fan_mode = "Orta"
        self._attr_current_temperature = 20
        self._attr_target_temperature = 22

    @property
    def name(self):
        return self._ac_name

    @property
    def supported_features(self):
        return ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE | ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF
    
    @property
    def temperature_unit(self):
        return UnitOfTemperature.CELSIUS

    @property
    def min_temp(self):
        return 16

    @property
    def max_temp(self):
        return 31

    @property
    def target_temperature_step(self):
        return 1

    @property
    def hvac_modes(self):
        return [HVACMode.OFF, HVACMode.COOL, HVACMode.FAN_ONLY, HVACMode.DRY, HVACMode.HEAT, HVACMode.HEAT_COOL]

    @property
    def hvac_mode(self):
        return self._attr_hvac_mode

    @property
    def fan_modes(self):
        return ['Otomatik', 'Sessiz', 'Düşük', 'Orta', 'Yüksek', 'En Yüksek']
    
    @property
    def fan_mode(self):
        return self._attr_fan_mode
    
    @property
    def current_temperature(self):
        return self._attr_current_temperature

    @property
    def target_temperature(self):
        return self._attr_target_temperature
    
    async def async_set_hvac_mode(self, hvac_mode: HVACMode):
        self._attr_hvac_mode = hvac_mode
        self.async_write_ha_state()

    async def async_set_fan_mode(self, fan_mode: str):
        self._attr_fan_mode = fan_mode
        self.async_write_ha_state()
    
    async def async_set_temperature(self, **kwargs):
        target_temperature = kwargs.get('temperature')
        if target_temperature is not None:
            self._attr_target_temperature = target_temperature
            # Burada API çağrısı yaparak gerçek cihaza komutu gönderebilirsiniz
            # Örneğin: await self._set_device_temperature(target_temperature)
            self.async_write_ha_state()

    async def async_turn_on(self):
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self):
        self._attr_is_on = False
        self.async_write_ha_state()