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

CONF_ACS = "acs"
CONF_AC_NAME = "name"
CONF_AC_TUYA_IR_DEVICE_ID = "tuya_ir_device_id"
CONF_AC_TUYA_DEVICE_LOCAL_KEY = "tuya_device_local_key"
CONF_AC_TUYA_DEVICE_IP = "tuya_device_ip"
CONF_AC_TUYA_DEVICE_VERSION = "tuya_device_version"
CONF_AC_TUYA_DEVICE_MODEL = "tuya_device_model"

DEFAULT_NAME = "TuyaIRAC"

AC_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_AC_NAME, default=DEFAULT_NAME): cv.string,
        vol.Required(CONF_AC_TUYA_IR_DEVICE_ID): cv.string,
        vol.Required(CONF_AC_TUYA_DEVICE_LOCAL_KEY): cv.string,
        vol.Required(CONF_AC_TUYA_DEVICE_IP): cv.string,
        vol.Required(CONF_AC_TUYA_DEVICE_VERSION, default='3.3'): cv.string,
        vol.Required(CONF_AC_TUYA_DEVICE_MODEL, default='MSZ-GE25VA'): cv.string,
    }
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ACS): vol.All(cv.ensure_list, [AC_SCHEMA]),
    }
)

HVAC_MODES = [HVACMode.AUTO, HVACMode.COOL, HVACMode.DRY, HVACMode.FAN_ONLY, HVACMode.HEAT, HVACMode.OFF]

FAN_MODES = ['Otomatik', 'Sessiz', 'Düşük', 'Orta', 'Yüksek', 'En Yüksek']

async def async_setup_platform(hass, config, async_add_entities, discovery_info = None):

    acs = [
        TuyaIRAC(hass, ac, FAN_MODES)
        for ac in config.get(CONF_ACS)
    ]

    async_add_entities(acs, update_before_add=True)


class TuyaIRAC(RestoreEntity, ClimateEntity):
    
    def __init__(self, hass, ac_conf, fan_modes):
        
        self._name = ac_conf[CONF_AC_NAME]
        self._hass = hass
        self._hvac_modes = HVAC_MODES
        self._fan_modes = fan_modes
        self._fan_mode = None
        self._fan_speed = 'medium'        
        self._hvac_mode = 'off'
        self._temp = 25

        self._api = IRApi(
            ac_conf[CONF_AC_TUYA_IR_DEVICE_ID],
            ac_conf[CONF_AC_TUYA_DEVICE_LOCAL_KEY],
            ac_conf[CONF_AC_TUYA_DEVICE_IP],
            ac_conf[CONF_AC_TUYA_DEVICE_VERSION],
            ac_conf[CONF_AC_TUYA_DEVICE_MODEL]
        )

        self._mutex = Lock()



    async def async_added_to_hass(self):
        
        await super().async_added_to_hass()
        
        await self._hass.async_add_executor_job(self._api.setup())

        prev = await self.async_get_last_state()
        
        if prev:
            
            self.mode = prev.attributes.get("internal_mode", None)

            self.temp = prev.attributes.get("internal_temp", None)

            self.fan_speed = prev.attributes.get("internal_fan_speed", None)

            if self.mode is None:
                self.mode = 'off'

            if self.temp is None:
                self.temp = 25

            if self.fan_speed is None:
                self.fan_speed = 'medium'


    @property
    def extra_state_attributes(self):
        return {
            "internal_mode": self.mode,
            "internal_fan_speed": self.fan_speed,
            "internal_temp": self.temp,
        }

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self) -> str:
        return f"climate {self._name}"

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
        value = self.temp
        if value is not None:
            value = int(value)
        return value

    @property
    def target_temperature(self):
        if self.mode == 'off':
            return None

        value = self.temp
        if value is not None:
            value = int(value)
        return value

    @property
    def target_temperature_step(self):
        return 1

    @property
    def hvac_mode(self):
        if self.mode == 'off':
            return HVACMode.OFF

        if self.mode == 'cool':
            return HVACMode.COOL

        if self.mode == 'heat':
            return HVACMode.HEAT

        if self.mode == 'auto':
            return HVACMode.HEAT_COOL

        if self.mode == 'fan':
            return HVACMode.FAN_ONLY

        if self.mode == 'dry':
            return HVACMode.DRY

        else:
            return HVACMode.OFF

    @property
    def hvac_modes(self):
        return [HVACMode.OFF, HVACMode.COOL, HVACMode.FAN_ONLY, HVACMode.DRY, HVACMode.HEAT, HVACMode.HEAT_COOL]

    @property
    def fan_mode(self):
        return self._fan_mode

    @property
    def fan_modes(self):
        return self._fan_modes

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
        self.temp = int(temperature)
        self._api.set_state(self.mode, self.temp, self.fan_speed)


    def set_hvac_mode(self, hvac_mode):

        ac_mode = None

        if hvac_mode == HVACMode.OFF:
            ac_mode = 'off'

        if hvac_mode == HVACMode.COOL:
            ac_mode = 'cool'

        if hvac_mode == HVACMode.HEAT:
            ac_mode = 'heat'

        if hvac_mode == HVACMode.HEAT_COOL:
            ac_mode = 'auto'

        if hvac_mode == HVACMode.FAN_ONLY:
            ac_mode = 'fan'

        if hvac_mode == HVACMode.DRY:
            ac_mode = 'dry'

        if ac_mode is None:
            return

        with self._act_and_update():
            self.run_with_lock(lambda: self._update_mode_critical(ac_mode))

    def _update_mode_critical(self, ac_mode):
        self.mode = ac_mode
        self._api.set_state(self.mode, self.temp, self.fan_speed)

    def set_fan_mode(self, fan_mode):

        fan_speed = None

        if fan_mode == 'Otomatik':
            fan_speed = 'auto'

        if fan_mode == 'Sessiz':
            fan_speed = 'quiet'

        if fan_mode == 'Düşük':
            fan_speed = 'low'

        if fan_mode == 'Orta':
            fan_speed = 'medium'

        if fan_mode == 'Yüksek':
            fan_speed = 'high'

        if fan_mode == 'En Yüksek':
            fan_speed = 'highest'                    

        if fan_speed is None:
            return
        
        self._fan_mode = fan_mode

        with self._act_and_update():
            self.run_with_lock(lambda: self._update_fan_speed_critical(fan_speed))

    def _update_fan_speed_critical(self, fan_speed):
        self.fan_speed = fan_speed
        self._api.set_state(self.mode, self.temp, self.fan_speed)


    @contextmanager
    def _act_and_update(self):
        yield

        asyncio.run_coroutine_threadsafe(
            self.async_update_ha_state(), self._hass.loop
        )

    def update(self):
        return