import utime
from ..base import BasePart
from ...global_vars import Var, BYTE, SYNC_CONFIG, COMMUNICATION_REQUEST_SEND, COMMUNICATION_RECV
from ...drivers import DriverMotor
from ...controller import Controller, FREQ_NORMAL


class Move(BasePart):
    """
    Модуль для керування рухом.
    Використовується для транспорту з єдиним мотором
    """
    freq_update = FREQ_NORMAL

    _motor: DriverMotor

    _move = Var(b'\xb0', BYTE, 0, -100, 100, params=(COMMUNICATION_RECV, ))

    _quadratic_control = Var(b'\xb1', float, 1, 0, 1, params=(SYNC_CONFIG, COMMUNICATION_REQUEST_SEND, COMMUNICATION_RECV))
    _delay_control = Var(b'\xb2', int, 0, params=(SYNC_CONFIG, ))

    _speed_kmh: float = 0
    _speed_coefficient: float = 0

    def __init__(
            self,
            motor: DriverMotor,
    ) -> None:
        super().__init__()
        self._motor = motor

    def _update(self, controller: Controller):
        move = self._get_value(self._move.get() / 100)
        if utime.ticks_diff(utime.ticks_ms(), self._move.get_last_update()) > self._delay_control.get():
            to_motor_value = 0
        else:
            to_motor_value = move

        if self._quadratic_control.get():
            to_motor_value = self._get_quadratic_value(to_motor_value)

        self._motor.motor_value(to_motor_value)

    @staticmethod
    def _get_quadratic_value(value):
        turn_d = 1 if value >= 0 else -1
        return (value ** 2) * turn_d

    @staticmethod
    def _get_value(value):
        if value < -1:
            return -1
        elif value > 1:
            return 1
        else:
            return value
