import asyncio
from threading import Lock
from contextlib import contextmanager
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.helpers.restore_state import RestoreEntity
import json5
import os
import codecs
import tinytuya

from homeassistant.const import (ATTR_TEMPERATURE, UnitOfTemperature)
from homeassistant.components.climate import (ClimateEntity, PLATFORM_SCHEMA)
from homeassistant.components.climate.const import (HVACMode, ClimateEntityFeature)

CONF_AC_NAME = "name"
CONF_DEVICE_ID = "tuya_ir_device_id"
CONF_DEVICE_LOCAL_KEY = "tuya_device_local_key"
CONF_DEVICE_IP = "tuya_device_ip"
CONF_DEVICE_VERSION = "tuya_device_version"
CONF_DEVICE_MODEL = "tuya_device_model"

DEFAULT_NAME = "Air Conditioner"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_AC_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_DEVICE_ID): cv.string,
    vol.Required(CONF_DEVICE_LOCAL_KEY): cv.string,
    vol.Required(CONF_DEVICE_IP): cv.string,
    vol.Required(CONF_DEVICE_VERSION, default='3.3'): cv.string,
    vol.Required(CONF_DEVICE_MODEL, default='MSZ-GE25VA'): cv.string,
})

current_dir = os.path.dirname(__file__)
commands_path1 = os.path.join(current_dir, './ac-commands-1.json5')
commands_path2 = os.path.join(current_dir, './ac-commands-2.json5')

with open(commands_path1, 'r') as f:
    ir_commands1 = json5.load(f)

with open(commands_path2, 'r') as f:
    ir_commands2 = json5.load(f)

async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    name = config.get(CONF_AC_NAME)
    device_id = config.get(CONF_DEVICE_ID)
    device_local_key = config.get(CONF_DEVICE_LOCAL_KEY)
    device_ip = config.get(CONF_DEVICE_IP)
    device_version = config.get(CONF_DEVICE_VERSION)
    device_model = config.get(CONF_DEVICE_MODEL)

    async_add_devices([
        TuyaIrClimate(hass, name, device_id, device_local_key, device_ip, device_version, device_model)
    ])


class TuyaIrClimate(RestoreEntity, ClimateEntity):
    
    def __init__(self, hass, name, device_id: str, device_local_key: str, device_ip: str, device_version: str, device_model: str):
        self.hass = hass
        self._enable_turn_on_off_backwards_compatibility = False
        self._name = name
        self._is_on = False
        self._hvac_mode = HVACMode.OFF
        self._fan_mode = "Orta"
        self._temp = 25
        self._device_id = device_id
        self._device_local_key = device_local_key
        self._device_ip = device_ip
        self._device_version = float('3.3' if device_version is None else device_version)
        self._device_api = None
        self._device_model = device_model
        self._mutex = Lock()

    def _setup_tuya(self):
        self._device_api = tinytuya.Device(self._device_id, self._device_ip, self._device_local_key, "default", 6, self._device_version)

    async def async_added_to_hass(self):
        
        await super().async_added_to_hass()
        
        await self.hass.async_add_executor_job(self._setup_tuya())

        prev = await self.async_get_last_state()
        
        if prev:
            self._is_on = prev.attributes.get("internal_is_on", False)
            self._hvac_mode = prev.attributes.get("internal_hvac_mode", HVACMode.OFF)
            self._temp = prev.attributes.get("internal_temp", 25)
            self._fan_mode = prev.attributes.get("internal_fan_mode", "Orta")

    @property
    def extra_state_attributes(self):
        return {
            "internal_is_on": self._is_on,
            "internal_hvac_mode": self._hvac_mode,
            "internal_temp": self._temp,            
            "internal_fan_mode": self._fan_mode,
        }



    @property
    def unique_id(self) -> str:
        return f"climate {self._name}"

    @property
    def should_poll(self):
        return False














    def run_with_lock(self, critical_section_fn):
        self._mutex.acquire(True)
        try:
            critical_section_fn()
        finally:
            self._mutex.release()

    def turn_on(self): 
        with self._act_and_update():
            self.run_with_lock(lambda: self._turn_on_critical())

    def _turn_on_critical(self):
        self._is_on = True
        self._set_state()

    def turn_off(self): 
        with self._act_and_update():
            self.run_with_lock(lambda: self._turn_off_critical())

    def _turn_off_critical(self):
        self._is_on = False
        self._set_state()

    def set_temperature(self, **kwargs):
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        temperature = int(temperature)
        if temperature < 16 or temperature > 31:
            return
        with self._act_and_update():
            self.run_with_lock(lambda: self._set_temperature_critical(temperature))

    def _set_temperature_critical(self, temperature):
        self._temp = temperature
        self._is_on = True
        self._set_state()

    def set_hvac_mode(self, hvac_mode):
        with self._act_and_update():
            self.run_with_lock(lambda: self._set_hvac_mode_critical(hvac_mode))

    def _set_hvac_mode_critical(self, hvac_mode):
        if hvac_mode is None:
            return
        self._hvac_mode = hvac_mode
        if self.hvac_mode == HVACMode.OFF:
            self._is_on = False
        else:
            self._is_on = True
        self._set_state()

    def set_fan_mode(self, fan_mode):
        if fan_mode is None:
            return
        with self._act_and_update():
            self.run_with_lock(lambda: self._set_fan_mode_critical(fan_mode))

    def _set_fan_mode_critical(self, fan_mode):
        self._fan_mode = fan_mode
        self._is_on = True
        self._set_state()

    def _set_state(self):

        if self._is_on == True and (self._hvac_mode == HVACMode.OFF or self._hvac_mode == None):
            self._hvac_mode = HVACMode.HEAT_COOL

        if self._hvac_mode == HVACMode.OFF or self._is_on == False:
            hvac_mode_key = "off"

        elif self._hvac_mode == HVACMode.HEAT_COOL or self._hvac_mode == HVACMode.AUTO:
            hvac_mode_key = "auto"

        elif self._hvac_mode == HVACMode.COOL:
            hvac_mode_key = "cool"

        elif self._hvac_mode == HVACMode.HEAT:
            hvac_mode_key = "heat"

        elif self._hvac_mode == HVACMode.DRY:
            hvac_mode_key = "dry"

        elif self._hvac_mode == HVACMode.FAN_ONLY:
            hvac_mode_key = "fan"

        else:
            msg = 'Mode must be one of off, cool, heat, dry, fan or auto'
            raise Exception(msg)


        if self._fan_mode == 'Otomatik':
            fan_mode_key = 'auto'

        elif self._fan_mode == 'Sessiz':
            fan_mode_key = 'quiet'

        elif self._fan_mode == 'Düşük':
            fan_mode_key = 'low'

        elif self._fan_mode == 'Orta':
            fan_mode_key = 'medium'

        elif self._fan_mode == 'Yüksek':
            fan_mode_key = 'high'

        elif self._fan_mode == 'En Yüksek':
            fan_mode_key = 'highest'                    

        else:
            msg = 'Fan mode must be one of Otomatik, Sessiz, Düşük, Orta, Yüksek or En Yüksek'
            raise Exception(msg)

        if hvac_mode_key == "off":
            if self._device_model == 'MSZ-GE25VA':
                ir_code = ir_commands1["off"]
            else:
                ir_code = ir_commands2["off"]
        else: 
            if self._device_model == 'MSZ-GE25VA':
                ir_code = ir_commands1[hvac_mode_key][fan_mode_key][str(self._temp)]
            else:
                ir_code = ir_commands2[hvac_mode_key][fan_mode_key][str(self._temp)]

        b64 = codecs.encode(codecs.decode(ir_code, 'hex'), 'base64').decode()
        
        payload = self._device_api.generate_payload(tinytuya.CONTROL, {"1": "study_key", "7": b64})
        
        self._device_api.send(payload)


    @contextmanager
    def _act_and_update(self):
        yield

        asyncio.run_coroutine_threadsafe(
            self.async_update_ha_state(), self.hass.loop
        )

    def update(self):
        return