import os
import json
import tinytuya
import json5
import codecs
import logging

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

    def _send_command(self, command_id: str):
        
        b64 = codecs.encode(codecs.decode(command_id, 'hex'), 'base64').decode()
        
        payload = self._device_api.generate_payload(tinytuya.CONTROL, {
            "1": "study_key", 
            "7": b64
        })
        
        res = self._device_api.send(payload)

        logger.debug("Send IR command result: %s", json.dumps(res, indent=2))

        if res is not None:
            logger.error("Send IR command failed with %s", res)

    def set_state(self, mode, temp, fan_speed):
        if mode not in ['off', 'cool', 'heat', 'dry', 'fan', 'auto']:
            msg = 'Mode must be one of off, cool, heat, dry, fan or auto, got ' + mode
            logger.error(msg)
            raise Exception(msg)

        if fan_speed not in ['auto', 'quiet', 'low', 'medium', 'high', 'highest']:
            msg = 'fan speed must be one of auto, quiet, low, medium, high or highest and instead got ' + fan_speed
            logger.error(msg)
            raise Exception(msg)

        if mode == "off":
            if self._device_model == 'MSZ-GE25VA':
                key_id = ir_commands1["off"]
            else:
                key_id = ir_commands2["off"]
        else: 
            if self._device_model == 'MSC-GE35VB':
                key_id = ir_commands1[mode][fan_speed][str(temp)]
            else:
                key_id = ir_commands2[mode][fan_speed][str(temp)]

        self._send_command(key_id)
