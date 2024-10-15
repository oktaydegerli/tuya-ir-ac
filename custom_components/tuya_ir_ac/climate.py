from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import HVACMode, ClimateEntityFeature
from homeassistant.const import UnitOfTemperature
from .const import (
    DOMAIN,
    CONF_AC_NAME,
    CONF_DEVICE_ID,
    CONF_DEVICE_LOCAL_KEY,
    CONF_DEVICE_IP,
    CONF_DEVICE_VERSION,
    CONF_DEVICE_MODEL,
)

import tinytuya
import os
import json5
import codecs
import logging
import threading

_LOGGER = logging.getLogger(__name__)

def load_json5_file(file_path):
    with open(file_path, 'r') as f:
        return json5.load(f)

async def async_setup_entry(hass, config_entry, async_add_entities):
    ac_name = config_entry.data.get(CONF_AC_NAME)
    device_id = config_entry.data.get(CONF_DEVICE_ID)
    device_local_key = config_entry.options.get(
        CONF_DEVICE_LOCAL_KEY, config_entry.data.get(CONF_DEVICE_LOCAL_KEY)
    )
    device_ip = config_entry.options.get(
        CONF_DEVICE_IP, config_entry.data.get(CONF_DEVICE_IP)
    )
    device_version = config_entry.options.get(
        CONF_DEVICE_VERSION, config_entry.data.get(CONF_DEVICE_VERSION)
    )
    device_model = config_entry.data.get(CONF_DEVICE_MODEL)

    current_dir = os.path.dirname(__file__)

    ir_codes = {
        "MSZ-GE25VA": await hass.async_add_executor_job(load_json5_file, os.path.join(current_dir, './MSZ-GE25VA.json5')),
        "MSC-GE35VB": await hass.async_add_executor_job(load_json5_file, os.path.join(current_dir, './MSC-GE35VB.json5')),
    }

    async_add_entities(
        [
            TuyaIrClimateEntity(
                ac_name,
                device_id,
                device_local_key,
                device_ip,
                device_version,
                device_model,
                ir_codes,
            )
        ]
    )

class TuyaIrClimateEntity(ClimateEntity):
    def __init__(
        self,
        ac_name,
        device_id,
        device_local_key,
        device_ip,
        device_version,
        device_model,
        ir_codes,
    ):
        self._ac_name = ac_name
        self._device_id = device_id
        self._device_local_key = device_local_key
        self._device_ip = device_ip
        self._device_version = device_version
        self._device_model = device_model
        self._ir_codes = ir_codes
        self._attr_hvac_mode = HVACMode.OFF
        self._attr_fan_mode = "Orta"
        self._attr_current_temperature = 20
        self._attr_target_temperature = 22
        self._lock = threading.Lock()

        # self._setup_tuya()

    def _setup_tuya(self):
        self._device_api = tinytuya.Device(
            self._device_id,
            self._device_ip,
            self._device_local_key,
            "default",
            5,
            self._device_version,
        )

    @property
    def unique_id(self) -> str:
        return f"{self._device_id}_{self._ac_name}"

    @property
    def name(self):
        return self._ac_name

    @property
    def supported_features(self):
        return (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.FAN_MODE
            | ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF
        )

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
        return [
            HVACMode.OFF,
            HVACMode.COOL,
            HVACMode.FAN_ONLY,
            HVACMode.DRY,
            HVACMode.HEAT,
            HVACMode.HEAT_COOL,
        ]

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
        if hvac_mode is not None:
            self._attr_hvac_mode = hvac_mode
            await self._set_state()

    async def async_set_fan_mode(self, fan_mode: str):
        if fan_mode is not None:
            self._attr_fan_mode = fan_mode
            if self._attr_hvac_mode == HVACMode.OFF or self._attr_hvac_mode is None:
                self._attr_hvac_mode = HVACMode.HEAT_COOL
            await self._set_state()

    async def async_set_temperature(self, **kwargs):
        target_temperature = kwargs.get('temperature')
        if target_temperature is not None:
            self._attr_target_temperature = int(target_temperature)
            if self._attr_hvac_mode == HVACMode.OFF or self._attr_hvac_mode is None:
                self._attr_hvac_mode = HVACMode.HEAT_COOL
            await self._set_state()

    async def async_turn_on(self):
        self._attr_hvac_mode = HVACMode.HEAT_COOL
        await self._set_state()

    async def async_turn_off(self):
        self._attr_hvac_mode = HVACMode.OFF
        await self._set_state()

    async def _set_state(self):
        if self._device_api is None:
            _LOGGER.error("Device API is not initialized")
            return

        self.async_write_ha_state()

        # Map HVAC modes
        hvac_mode_mapping = {
            HVACMode.OFF: "off",
            HVACMode.HEAT_COOL: "auto",
            HVACMode.COOL: "cool",
            HVACMode.HEAT: "heat",
            HVACMode.DRY: "dry",
            HVACMode.FAN_ONLY: "fan",
        }

        hvac_mode_key = hvac_mode_mapping.get(self._attr_hvac_mode)
        if hvac_mode_key is None:
            msg = 'Mode must be one of off, cool, heat, dry, fan, or auto'
            _LOGGER.error(msg)
            return

        # Map fan modes
        fan_mode_mapping = {
            'Otomatik': 'auto',
            'Sessiz': 'quiet',
            'Düşük': 'low',
            'Orta': 'medium',
            'Yüksek': 'high',
            'En Yüksek': 'highest',
        }

        fan_mode_key = fan_mode_mapping.get(self._attr_fan_mode)
        if fan_mode_key is None:
            msg = (
                'Fan mode must be one of Otomatik, Sessiz, Düşük, Orta, Yüksek, or En Yüksek'
            )
            _LOGGER.error(msg)
            return

        # Select the appropriate IR codes based on the device model
        ir_codes = self._ir_codes.get(self._device_model)
        if ir_codes is None:
            _LOGGER.error("No IR codes found for device model %s", self._device_model)
            return

        if hvac_mode_key == "off":
            ir_code = ir_codes["off"]
        else:
            temp_str = str(self._attr_target_temperature)
            try:
                ir_code = ir_codes[hvac_mode_key][fan_mode_key][temp_str]
            except KeyError:
                _LOGGER.error(
                    "IR code not found for mode: %s, fan: %s, temp: %s",
                    hvac_mode_key,
                    fan_mode_key,
                    temp_str,
                )
                return

        b64 = codecs.encode(codecs.decode(ir_code, 'hex'), 'base64').decode()

        payload = self._device_api.generate_payload(
            tinytuya.CONTROL, {"1": "study_key", "7": b64}
        )

        with self._lock:
            res = await self.hass.async_add_executor_job(self._device_api.send, payload)

        if res is not None:
            _LOGGER.error("Error sending payload: %s", res)
