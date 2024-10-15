from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (HVACMode, ClimateEntityFeature)
from homeassistant.const import (ATTR_TEMPERATURE, UnitOfTemperature)
from .const import DOMAIN, CONF_AC_NAME, CONF_DEVICE_ID, CONF_DEVICE_LOCAL_KEY, CONF_DEVICE_IP, CONF_DEVICE_VERSION, CONF_DEVICE_MODEL
from threading import Lock
import tinytuya
import os
import json5
import codecs
import logging

_LOGGER = logging.getLogger(__name__)

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
        self._mutex = Lock()
        
        self._setup_tuya()

    def _setup_tuya(self): 
        self._device_api = None
        self._ir_codes1 = None
        self._ir_codes2 = None

        current_dir = os.path.dirname(__file__)
        commands_path1 = os.path.join(current_dir, './ac-commands-1.json5')
        commands_path2 = os.path.join(current_dir, './ac-commands-2.json5')

        with open(commands_path1, 'r') as f:
            self._ir_codes1 = json5.load(f)

        with open(commands_path2, 'r') as f:
            self._ir_codes2 = json5.load(f)

        self._device_api = tinytuya.Device(self._device_id, self._device_ip, self._device_local_key, "default", 5, self._device_version)

    @property
    def unique_id(self) -> str:
        return f"{self._device_id}_{self._ac_name}"

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
        self.run_with_lock(lambda: self._set_state())

    async def async_set_fan_mode(self, fan_mode: str):
        self._attr_fan_mode = fan_mode
        self.run_with_lock(lambda: self._set_state())
    
    async def async_set_temperature(self, **kwargs):
        target_temperature = kwargs.get('temperature')
        if target_temperature is not None:
            self._attr_target_temperature = target_temperature
            self.run_with_lock(lambda: self._set_state())

    async def async_turn_on(self):
        self._attr_is_on = True
        self.run_with_lock(lambda: self._set_state())

    async def async_turn_off(self):
        self._attr_is_on = False
        self.run_with_lock(lambda: self._set_state())

    def run_with_lock(self, critical_section_fn):
        self._mutex.acquire(True)
        try:
            critical_section_fn()
        finally:
            self._mutex.release() 

    def _set_state(self):

        if self._device_api is None:
            _LOGGER.error("DeviceApi is not initialized")

        if self._attr_is_on == True and (self._attr_hvac_mode == HVACMode.OFF or self._attr_hvac_mode == None):
            self._attr_hvac_mode = HVACMode.HEAT_COOL

        self.async_write_ha_state()

        if self._attr_hvac_mode == HVACMode.OFF or self._attr_is_on == False:
            hvac_mode_key = "off"

        elif self._attr_hvac_mode == HVACMode.HEAT_COOL or self._attr_hvac_mode == HVACMode.AUTO:
            hvac_mode_key = "auto"

        elif self._attr_hvac_mode == HVACMode.COOL:
            hvac_mode_key = "cool"

        elif self._attr_hvac_mode == HVACMode.HEAT:
            hvac_mode_key = "heat"

        elif self._attr_hvac_mode == HVACMode.DRY:
            hvac_mode_key = "dry"

        elif self._attr_hvac_mode == HVACMode.FAN_ONLY:
            hvac_mode_key = "fan"

        else:
            msg = 'Mode must be one of off, cool, heat, dry, fan or auto'
            raise Exception(msg)


        if self._attr_fan_mode == 'Otomatik':
            fan_mode_key = 'auto'

        elif self._attr_fan_mode == 'Sessiz':
            fan_mode_key = 'quiet'

        elif self._attr_fan_mode == 'Düşük':
            fan_mode_key = 'low'

        elif self._attr_fan_mode == 'Orta':
            fan_mode_key = 'medium'

        elif self._attr_fan_mode == 'Yüksek':
            fan_mode_key = 'high'

        elif self._attr_fan_mode == 'En Yüksek':
            fan_mode_key = 'highest'                    

        else:
            msg = 'Fan mode must be one of Otomatik, Sessiz, Düşük, Orta, Yüksek or En Yüksek'
            raise Exception(msg)

        if hvac_mode_key == "off":
            if self._device_model == 'MSZ-GE25VA':
                ir_code = self._ir_codes1["off"]
            else:
                ir_code = self._ir_codes2["off"]
        else: 
            if self._device_model == 'MSZ-GE25VA':
                ir_code = self._ir_codes1[hvac_mode_key][fan_mode_key][str(self._temp)]
            else:
                ir_code = self._ir_codes2[hvac_mode_key][fan_mode_key][str(self._temp)]

        b64 = codecs.encode(codecs.decode(ir_code, 'hex'), 'base64').decode()
        
        payload = self._device_api.generate_payload(tinytuya.CONTROL, {"1": "study_key", "7": b64})
        
        res = self._device_api.send(payload)

        if res is not None:
            _LOGGER.error("Send IR command failed with %s", res)   