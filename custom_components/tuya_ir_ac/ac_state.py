
MODE_ATTR = 'mode'
FAN_SPEED_ATTR = 'fan_speed'
TEMP_ATTR = 'temp'


class ACState:
    def __init__(self, entity, hass):
        self._hass = hass
        self._entity = entity
        self._mode = 'off'
        self._fan_speed = 'low'
        self._temp = 25

    def get_entity_id(self, attribute):
        return f'{self._entity.unique_id}.{attribute}'


    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, value):
        if value not in ['off', 'cool', 'heat', 'dry', 'fan', 'auto']:
            raise ValueError('Mode must be one of off, cool, heat, dry, fan or auto, got ' + value)

        self._mode = value

    @property
    def fan_speed(self):
        return self._fan_speed

    @fan_speed.setter
    def fan_speed(self, value):
        if value not in ['low', 'medium', 'high', 'auto']:
            raise ValueError('fan speed must be one of low, medium, high or auto and instead got ' + value)

        self._fan_speed = value

    @property
    def temp(self):
        return self._temp

    @temp.setter
    def temp(self, value):
        if value < 16 or value > 31:
            raise ValueError('temp must be between 16 and 31, got ' + str(value))

        self._temp = value

    def set_initial_state(self, mode, temp, fan_speed):

        if mode is None:
            mode = 'off'

        self.mode = mode

        if temp is None:
            temp = 25

        self.temp = temp

        if fan_speed is None:
            fan_speed = 'low'

        self.fan_speed = fan_speed
