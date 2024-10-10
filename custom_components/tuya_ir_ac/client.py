import logging
from .ac_state import ACState
from .ir_api import IRApi

logger = logging.getLogger(__name__ + ".client")

class AC:
    def __init__(self, ir_device_id: str, device_local_key: str, device_ip: str, version: str, state: ACState):
        self._api = IRApi(ir_device_id, device_local_key, device_ip, version)
        self._state = state
        self._status = None
        self._model = None

    def setup(self):
        self._api.setup()

    def update_temp(self, new_temp):
        res = self._api.set_state(self._state.mode, new_temp, self._state.fan_speed)
        self._update_from_result(res)

    def update_mode(self, new_mode):
        res = self._api.set_state(new_mode, self._state.temp, self._state.fan_speed)
        self._update_from_result(res)

    def update_fan_speed(self, new_fan_speed):
        res = self._api.set_state(self._state.mode, self._state.temp, new_fan_speed)
        self._update_from_result(res)

    def _update_from_result(self, res):
        self._state.is_on = True
        self._state.mode = res["mode"]
        self._state.fan_speed = res["fan_speed"]
        self._state.temp = int(res["temp"])

    def turn_on(self):
        self._api.power_on()
        self._state.is_on = True

    def turn_off(self):
        self._api.power_off()
        self._state.is_on = False
