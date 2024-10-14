import asyncio
import logging
from contextlib import contextmanager
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.helpers.restore_state import RestoreEntity
from typing import Callable
from .ac_state import ACState
from .client import AC

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

FAN_MODES = ['Otomatik', 'Sessiz', 'Düşük', 'Orta', 'Yüksek', 'En Yüksek']

async def async_setup_platform(hass, config, async_add_entities: Callable, discovery_info = None) -> None:

    acs = [
        TuyaIRAC(hass, ac, FAN_MODES)
        for ac in config.get(CONF_ACS)
    ]

    async_add_entities(acs, update_before_add=True)


class TuyaIRAC(RestoreEntity, ClimateEntity):
    def __init__(self, hass, ac_conf, fan_modes):
        self._name = ac_conf[CONF_AC_NAME]
        self._hass = hass
        self._state = ACState(self, self._hass)
        self._fan_mode = None
        self._fan_modes = fan_modes
        self.ac = AC(
            ac_conf[CONF_AC_TUYA_IR_DEVICE_ID],
            ac_conf[CONF_AC_TUYA_DEVICE_LOCAL_KEY],
            ac_conf[CONF_AC_TUYA_DEVICE_IP],
            ac_conf[CONF_AC_TUYA_DEVICE_VERSION],
            ac_conf[CONF_AC_TUYA_DEVICE_MODEL],
            self._state
        )


    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        await self._hass.async_add_executor_job(self.ac.setup)
        prev = await self.async_get_last_state()
        if prev:
            self._state.set_initial_state(prev.attributes.get("internal_mode", None), prev.attributes.get("internal_temp", None), prev.attributes.get("internal_fan_speed", None))

    @property
    def extra_state_attributes(self):
        return {
            "internal_mode": self._state.mode,
            "internal_fan_speed": self._state.fan_speed,
            "internal_temp": self._state.temp,
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
        value = self._state.temp
        if value is not None:
            value = int(value)
        return value

    @property
    def target_temperature(self):
        if self._state.mode == 'off':
            return None

        value = self._state.temp
        if value is not None:
            value = int(value)
        return value

    @property
    def target_temperature_step(self):
        return 1

    @property
    def hvac_mode(self):
        if self._state.mode == 'off':
            return HVACMode.OFF

        if self._state.mode == 'cool':
            return HVACMode.COOL

        if self._state.mode == 'heat':
            return HVACMode.HEAT

        if self._state.mode == 'auto':
            return HVACMode.HEAT_COOL

        if self._state.mode == 'fan':
            return HVACMode.FAN_ONLY

        if self._state.mode == 'dry':
            return HVACMode.DRY

        else:
            return HVACMode.OFF

    @property
    def hvac_modes(self):
        return [
            HVACMode.OFF,
            HVACMode.COOL,
            HVACMode.FAN_ONLY,
            HVACMode.DRY,
            HVACMode.HEAT,
            HVACMode.HEAT_COOL,
        ]

    @property
    def fan_mode(self):
        return self._fan_mode

    @property
    def fan_modes(self):
        return self._fan_modes

    @property
    def supported_features(self):
        return ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE

    def set_temperature(self, **kwargs):
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        temperature = int(temperature)
        with self._act_and_update():
            self.ac.update_temp(temperature)

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
            self.ac.update_mode(ac_mode)


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
            self.ac.update_fan_speed(fan_speed)

    @contextmanager
    def _act_and_update(self):
        yield

        asyncio.run_coroutine_threadsafe(
            self.async_update_ha_state(), self._hass.loop
        )

    def update(self):
        return