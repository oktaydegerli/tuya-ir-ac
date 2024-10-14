import os
import json
import tinytuya
import json5
import codecs
import logging
from homeassistant.components.climate.const import (HVACMode, ClimateEntityFeature)

logger = logging.getLogger(__name__ + ".client.ir_api")

# Read from json file

current_dir = os.path.dirname(__file__)
commands_path1 = os.path.join(current_dir, './ac-commands-1.json5')
commands_path2 = os.path.join(current_dir, './ac-commands-2.json5')

with open(commands_path1, 'r') as f:
    ir_commands1 = json5.load(f)

with open(commands_path2, 'r') as f:
    ir_commands2 = json5.load(f)

class IRApi:
    def __init__(self, ir_device_id: str, device_local_key: str, device_ip: str, version: str = '3.3', device_model: str = 'MSZ-GE25VA'):
        self.ir_device_id = ir_device_id
        self.device_local_key = device_local_key
        self.device_ip = device_ip
        self.version = float('3.3' if version is None else version)
        self._device_api = None
        self._device_model = device_model

    def setup(self):
        self._device_api = tinytuya.Device(self.ir_device_id, self.device_ip, self.device_local_key)
        self._device_api.set_version(self.version)

    def set_state(self, hvac_mode, temperature, fan_mode):

        hvac_mode_key = None

        if hvac_mode == HVACMode.OFF:
            hvac_mode_key = "off"

        if hvac_mode == HVACMode.COOL:
            hvac_mode_key = "cool"

        if hvac_mode == HVACMode.HEAT:
            hvac_mode_key = "heat"

        if hvac_mode == HVACMode.AUTO:
            hvac_mode_key = "auto"

        if hvac_mode == HVACMode.HEAT_COOL:
            hvac_mode_key = "auto"

        if hvac_mode == HVACMode.DRY:
            hvac_mode_key = "dry"

        if hvac_mode == HVACMode.FAN_ONLY:
            hvac_mode_key = "fan"

        if hvac_mode_key == None:
            msg = 'Mode must be one of off, cool, heat, dry, fan or auto'
            logger.error(msg)
            raise Exception(msg)
        
        fan_mode_key = None

        if fan_mode == 'Otomatik':
            fan_mode_key = 'auto'

        if fan_mode == 'Sessiz':
            fan_mode_key = 'quiet'

        if fan_mode == 'Düşük':
            fan_mode_key = 'low'

        if fan_mode == 'Orta':
            fan_mode_key = 'medium'

        if fan_mode == 'Yüksek':
            fan_mode_key = 'high'

        if fan_mode == 'En Yüksek':
            fan_mode_key = 'highest'                    

        if fan_mode_key is None:
            msg = 'Fan mode must be one of Otomatik, Sessiz, Düşük, Orta, Yüksek or En Yüksek'
            logger.error(msg)
            raise Exception(msg)

        if hvac_mode_key == "off":
            if self._device_model == 'MSZ-GE25VA':
                ir_code = ir_commands1["off"]
            else:
                ir_code = ir_commands2["off"]
        else: 
            if self._device_model == 'MSZ-GE25VA':
                ir_code = ir_commands1[hvac_mode_key][fan_mode_key][str(temperature)]
            else:
                ir_code = ir_commands2[hvac_mode_key][fan_mode_key][str(temperature)]

        b64 = codecs.encode(codecs.decode(ir_code, 'hex'), 'base64').decode()
        
        payload = self._device_api.generate_payload(tinytuya.CONTROL, {"1": "study_key", "7": b64})
        
        res = self._device_api.send(payload)

        logger.debug("Send IR command result: %s", json.dumps(res, indent=2))

        if res is not None:
            logger.error("Send IR command failed with %s", res)
