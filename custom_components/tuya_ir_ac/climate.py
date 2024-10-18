from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import HVACMode, ClimateEntityFeature
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.event import async_track_state_change
from homeassistant.helpers import config_validation as cv
from .const import DOMAIN, CONF_AC_NAME, CONF_DEVICE_ID, CONF_DEVICE_LOCAL_KEY, CONF_DEVICE_IP, CONF_DEVICE_VERSION, CONF_DEVICE_MODEL, CONF_TEMPERATURE_SENSOR

import tinytuya
import os
import json
import codecs
import logging
import threading

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):

    def get_config_value(key):
        return config_entry.options.get(key, config_entry.data.get(key))

    ac_name = get_config_value(CONF_AC_NAME)
    device_id = get_config_value(CONF_DEVICE_ID)
    device_model = get_config_value(CONF_DEVICE_MODEL)
    device_local_key = get_config_value(CONF_DEVICE_LOCAL_KEY)
    device_ip = get_config_value(CONF_DEVICE_IP)
    device_version = get_config_value(CONF_DEVICE_VERSION)
    temperature_sensor = get_config_value(CONF_TEMPERATURE_SENSOR)

    if any(value is None for value in [ac_name, device_id, device_model, device_local_key, device_ip, device_version]):
        hass.async_create_task(
            hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "Tuya IR Climate Entegrasyon Hatası",
                    "message": "Gerekli config seçenekleri eksik. Lütfen entegrasyonu kontrol edin.",
                },
            )
        )
        return False

    await async_add_entities([TuyaIrClimateEntity(hass, ac_name, device_id, device_local_key, device_ip, device_version, device_model, temperature_sensor)])
    return True

class TuyaIrClimateEntity(ClimateEntity, RestoreEntity):
    def __init__(self, hass, ac_name, device_id, device_local_key, device_ip, device_version, device_model, temperature_sensor):
        self._enable_turn_on_off_backwards_compatibility = False
        self.hass = hass
        self._ac_name = ac_name
        self._device_id = device_id
        self._device_local_key = device_local_key
        self._device_ip = device_ip
        self._device_version = device_version
        self._device_model = device_model
        self._temperature_sensor = temperature_sensor
        self._attr_hvac_mode = HVACMode.OFF
        self._attr_fan_mode = "Orta"
        self._attr_target_temperature = 22
        self._attr_current_temperature = 20
        self._lock = threading.Lock()
        self._device_api = None
        self._unsub_state_changed = None
        self._ir_codes = {}
        self._commands_path = os.path.join(self.hass.config.path(), "custom_components", DOMAIN, f'{self._device_model}.json')

    async def _async_get_device_api(self):
        async with self._lock:
            if self._device_api is None:
                try:
                    self._device_api = await self.hass.async_add_executor_job(tinytuya.Device, self._device_id, self._device_ip, self._device_local_key, "default", 5, self._device_version)
                except Exception as e:
                    _LOGGER.error(f"Tuya cihazı oluşturma hatası: {e}")
                    return None
            return self._device_api

    async def async_added_to_hass(self):

        await super().async_added_to_hass()

        try:
            with open(self._commands_path, 'r') as file:
                self._ir_codes = json.load(file)
        except FileNotFoundError:
            _LOGGER.error(f"IR kod dosyası bulunamadı: {self._commands_path}")
            return

        last_state = await self.async_get_last_state()
        if last_state is not None:
            self._attr_hvac_mode = last_state.state
            self._attr_fan_mode = last_state.attributes.get('fan_mode')
            self._attr_target_temperature = last_state.attributes.get('temperature')

        if self._temperature_sensor:
            self._unsub_state_changed = async_track_state_change(self.hass, self._temperature_sensor, self._async_sensor_changed)

    async def async_will_remove_from_hass(self):
        if self._unsub_state_changed:
            self._unsub_state_changed()
            self._unsub_state_changed = None      

    async def _async_sensor_changed(self, entity_id, old_state, new_state):
        if new_state is None:
            return
        try:
                self._attr_current_temperature = float(new_state.state)
                self.async_write_ha_state()
        except (TypeError, ValueError) as e:
                _LOGGER.warning(f"Geçersiz sıcaklık sensörü değeri: {new_state.state} - Hata: {e}")


    @property
    def unique_id(self) -> str:
        return f"{self._device_id}"

    @property
    def name(self):
        return self._ac_name

    @property
    def supported_features(self):
        return (ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE |
                ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF)

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
        await self._set_state()

    async def async_set_fan_mode(self, fan_mode: str):
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

        if self._attr_hvac_mode == HVACMode.OFF:
            hvac_mode_key = "off"
        elif self._attr_hvac_mode == HVACMode.HEAT_COOL:
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
            ir_code = self._ir_codes.get("off")
        else:
            ir_code = self._ir_codes.get(hvac_mode_key, {}).get(fan_mode_key, {}).get(str(self._attr_target_temperature))

        if ir_code is None:
            _LOGGER.error(f"Geçersiz HVAC modu, fan modu veya hedef sıcaklık kombinasyonu.")
            return

        b64 = codecs.encode(codecs.decode(ir_code, 'hex'), 'base64').decode()
        command = {"1": "study_key", "7": b64}

        try:
            await self._async_send_command(command)
        except Exception as e:
            _LOGGER.error(f"Durum ayarlama hatası: {e}")


    async def _async_send_command(self, command):
        device_api = await self._async_get_device_api()
        if device_api is None:
            _LOGGER.error("Tuya cihazı mevcut değil.")
            return

        try:
            payload = device_api.generate_payload(tinytuya.CONTROL, command)
            await self.hass.async_add_executor_job(device_api.send, payload)
        except Exception as e:
            _LOGGER.error(f"Komut gönderme hatası: {e}")