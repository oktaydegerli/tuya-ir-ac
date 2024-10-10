from threading import Lock
import logging
from .ac_state import ACState
from .ir_api import IRApi

logger = logging.getLogger(__name__ + ".client")

class AC:
    def __init__(self, ir_device_id: str, device_local_key: str, device_ip: str, version: str, state: ACState):
        self._api = IRApi(ir_device_id, device_local_key, device_ip, version)
        self._mutex = Lock()
        self._state = state
        self._status = None
        self._model = None

    def setup(self):
        self._api.setup()

    def update_temp(self, new_temp):
        self.run_with_lock(lambda: self._update_temp_critical(new_temp))

    def _update_temp_critical(self, new_temp):
        self._state.is_on = True
        self._state.temp = int(new_temp)
        self._api.set_state(self._state.mode, self._state.temp, self._state.fan_speed)

    def update_mode(self, new_mode):
        self.run_with_lock(lambda: self._update_mode_critical(new_mode))

    def _update_mode_critical(self, new_mode):
        self._state.is_on = True
        self._state.mode = new_mode
        self._api.set_state(self._state.mode, self._state.temp, self._state.fan_speed)

    def update_fan_speed(self, new_fan_speed):
        self.run_with_lock(lambda: self._update_fan_speed_critical(new_fan_speed))

    def _update_fan_speed_critical(self, new_fan_speed):
        self._state.is_on = True
        self._state.fan_speed = new_fan_speed
        self._api.set_state(self._state.mode, self._state.temp, self._state.fan_speed)

    def turn_on(self):
        self.run_with_lock(lambda: self._turn_on_critical())

    def _turn_on_critical(self):
        self._api.power_on()
        self._state.is_on = True

    def turn_off(self):
        self.run_with_lock(lambda: self._turn_off_critical())

    def _turn_off_critical(self):
        self._api.power_off()
        self._state.is_on = False

    def run_with_lock(self, critical_section_fn):
        self._mutex.acquire(True)
        try:
            critical_section_fn()
        finally:
            self._mutex.release()
