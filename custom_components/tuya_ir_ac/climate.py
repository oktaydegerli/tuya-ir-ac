import asyncio
from threading import Lock
from contextlib import contextmanager
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.helpers.restore_state import RestoreEntity
from .ir_api import IRApi

from homeassistant.const import (ATTR_TEMPERATURE, UnitOfTemperature)
from homeassistant.components.climate import (ClimateEntity, PLATFORM_SCHEMA)
from homeassistant.components.climate.const import (HVACMode, ClimateEntityFeature)

CONF_AC_NAME = "name"
CONF_AC_TUYA_IR_DEVICE_ID = "tuya_ir_device_id"
CONF_AC_TUYA_DEVICE_LOCAL_KEY = "tuya_device_local_key"
CONF_AC_TUYA_DEVICE_IP = "tuya_device_ip"
CONF_AC_TUYA_DEVICE_VERSION = "tuya_device_version"
CONF_AC_TUYA_DEVICE_MODEL = "tuya_device_model"

DEFAULT_NAME = "TuyaIRAC"


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_AC_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_AC_TUYA_IR_DEVICE_ID): cv.string,
    vol.Required(CONF_AC_TUYA_DEVICE_LOCAL_KEY): cv.string,
    vol.Required(CONF_AC_TUYA_DEVICE_IP): cv.string,
    vol.Required(CONF_AC_TUYA_DEVICE_VERSION, default='3.3'): cv.string,
    vol.Required(CONF_AC_TUYA_DEVICE_MODEL, default='MSZ-GE25VA'): cv.string,
})


async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    name = config.get(CONF_AC_NAME)
    device_id = config.get(CONF_AC_TUYA_IR_DEVICE_ID)
    local_key = config.get(CONF_AC_TUYA_DEVICE_LOCAL_KEY)
    device_ip = config.get(CONF_AC_TUYA_DEVICE_IP)
    device_version = config.get(CONF_AC_TUYA_DEVICE_VERSION)
    device_model = config.get(CONF_AC_TUYA_DEVICE_MODEL)

    async_add_devices([
        TuyaIRAC(hass, name, device_id, local_key, device_ip, device_version, device_model)
    ])


class TuyaIRAC(RestoreEntity, ClimateEntity):
    
    def __init__(self, hass, name, device_id: str, local_key: str, device_ip: str, device_version: str, device_model: str):
        self.hass = hass
        self._name = name
        self._fan_mode = "Düşük"
        self._hvac_mode = HVACMode.OFF
        self._temp = 25
        self._unique_id = 'climate.tuya_ir_ac_' + device_ip.decode('utf-8').lower()
        self._mutex = Lock()
        self._api = IRApi(device_id, local_key, device_ip, device_version, device_model)

    async def async_added_to_hass(self):
        
        await super().async_added_to_hass()
        
        await self.hass.async_add_executor_job(self._api.setup())

        prev = await self.async_get_last_state()
        
        if prev:
            self._hvac_mode = prev.attributes.get("internal_mode", None)
            self._temp = prev.attributes.get("internal_temp", None)
            self._fan_mode = prev.attributes.get("internal_fan_mode", None)

            if self._hvac_mode is None:
                self._hvac_mode = HVACMode.OFF

            if self._temp is None:
                self._temp = 25

            if self._fan_mode is None:
                self._fan_mode = 'Düşük'


    @property
    def extra_state_attributes(self):
        return {
            "internal_mode": self._hvac_mode,
            "internal_fan_mode": self._fan_mode,
            "internal_temp": self._temp,
        }

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        # Return unique_id
        return self._unique_id

    @property
    def should_poll(self):
        return False

    @property
    def min_temp(self):
        return 16

    @property
    def max_temp(self):
        return 31

    @property
    def temperature_unit(self):
        return UnitOfTemperature.CELSIUS

    @property
    def current_temperature(self):
        value = self._temp
        if value is not None:
            value = int(value)
        return value

    @property
    def target_temperature(self):
        if self._hvac_mode == HVACMode.OFF:
            return None

        value = self._temp
        if value is not None:
            value = int(value)
        return value

    @property
    def target_temperature_step(self):
        return 1

    @property
    def hvac_mode(self):
        return self._hvac_mode

    @property
    def hvac_modes(self):
        return [HVACMode.OFF, HVACMode.COOL, HVACMode.FAN_ONLY, HVACMode.DRY, HVACMode.HEAT, HVACMode.HEAT_COOL]

    @property
    def fan_mode(self):
        return self._fan_mode

    @property
    def fan_modes(self):
        return ['Otomatik', 'Sessiz', 'Düşük', 'Orta', 'Yüksek', 'En Yüksek']

    @property
    def supported_features(self):
        return ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE


    def run_with_lock(self, critical_section_fn):
        self._mutex.acquire(True)
        try:
            critical_section_fn()
        finally:
            self._mutex.release()


    def set_temperature(self, **kwargs):
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        temperature = int(temperature)
        if temperature < 16 or temperature > 31:
            return
        with self._act_and_update():
            self.run_with_lock(lambda: self._update_temp_critical(temperature))

    def _update_temp_critical(self, temperature):
        self._temp = int(temperature)
        self._api.set_state(self._hvac_mode, self._temp, self._fan_mode)


    def set_hvac_mode(self, hvac_mode):
        with self._act_and_update():
            self.run_with_lock(lambda: self._update_mode_critical(hvac_mode))

    def _update_mode_critical(self, hvac_mode):
        self._hvac_mode = hvac_mode
        self._api.set_state(self._hvac_mode, self._temp, self._fan_mode)

    def set_fan_mode(self, fan_mode):
        with self._act_and_update():
            self.run_with_lock(lambda: self._update_fan_mode_critical(fan_mode))

    def _update_fan_mode_critical(self, fan_mode):
        self._fan_mode = fan_mode
        self._api.set_state(self._hvac_mode, self._temp, self._fan_mode)


    @contextmanager
    def _act_and_update(self):
        yield

        asyncio.run_coroutine_threadsafe(
            self.async_update_ha_state(), self.hass.loop
        )

    def update(self):
        return