from ..base import BasePart
from global_vars import Var, BYTE, SYNC_CONFIG, COMMUNICATION_REQUEST_SEND, COMMUNICATION_RECV
from drivers import DriverGyro, DriverPWMServo, DriverDirectionEncoder
from controller import Controller, FREQ_NORMAL
from .dashboard import Dashboard


class Turn(BasePart):
    """
    Модуль для керування поворотами.
    Використовується для класичного транспорту з єдиною поворотною вісю
    """
    freq_update = FREQ_NORMAL
    _turn = Var(b'\xa0', BYTE, 0, -100, 100, params=(COMMUNICATION_RECV, ))

    _left_servo_position = Var(b'\xd0', float, 0, 0, 1, params=(SYNC_CONFIG, COMMUNICATION_REQUEST_SEND, COMMUNICATION_RECV))
    _null_servo_position = Var(b'\xd1', float, 0.5, 0, 1, params=(SYNC_CONFIG, COMMUNICATION_REQUEST_SEND, COMMUNICATION_RECV))
    _right_servo_position = Var(b'\xd2', float, 1, 0, 1, params=(SYNC_CONFIG, COMMUNICATION_REQUEST_SEND, COMMUNICATION_RECV))
    _quadratic_control = Var(b'\xd3', bool, False, params=(SYNC_CONFIG, COMMUNICATION_REQUEST_SEND, COMMUNICATION_RECV))
    _stability_control = Var(b'\xd4', bool, False, params=(SYNC_CONFIG, COMMUNICATION_REQUEST_SEND, COMMUNICATION_RECV))

    _servo: DriverPWMServo
    _gyro: DriverGyro
    _direction_encoder: DriverDirectionEncoder

    __turn_coefficient: float = 0

    def __init__(
            self,
            servo: DriverPWMServo,
            gyro: DriverGyro = None,
            direction_encoder: DriverDirectionEncoder = None,
    ) -> None:
        super().__init__()
        self._servo = servo
        self._gyro = gyro
        self._direction_encoder = direction_encoder

    def _update(self, controller: Controller):
        dashboard: Dashboard = controller.get_part(Dashboard)
        turn = self._get_correct_turn(self._turn.get() / 100)
        degrees_second = 0
        speed_coefficient = 0
        if self._quadratic_control.get():
            turn = self._get_quadratic_value(turn)
        if self._gyro and self._direction_encoder:
            degrees_second = self._direction_encoder.get_direction() * self._gyro.get_gyro_z()
        if dashboard:
            speed_coefficient = dashboard.get_speed(True)

        # Поки у форматі милиці
        if self._stability_control.get() and turn == 0 and degrees_second != 0 and speed_coefficient > 0:
            _vc = degrees_second / 250
            direction = 1 if _vc >= 0 else -1
            _vc = abs(_vc)
            _v = (_vc ** (1 / 2) / (1 + 2 * speed_coefficient))
            # _v = (_vc**(1/9) / 6)
            # _v += _vc ** 1.5
            if _v > 1:
                _v = 1
            elif _v < 0:
                _v = 0
            self.__turn_coefficient = _v * direction
        elif turn != 0 or speed_coefficient <= 0:
            self.__turn_coefficient = 0

        position = self._get_turn_servo_position(turn + self.__turn_coefficient)
        self._servo.set_position(position)

    @staticmethod
    def _get_quadratic_value(value):
        turn_d = 1 if value >= 0 else -1
        return (value ** 2) * turn_d

    def _get_turn_servo_position(self, turn) -> float:
        if turn < 0:
            _turn = -turn
            position = self._left_servo_position.get() * _turn + (self._null_servo_position.get()) * (1 - _turn)
            return position
        elif turn > 0:
            _turn = turn
            position = self._right_servo_position.get() * _turn + (self._null_servo_position.get()) * (1 - _turn)
            return position
        else:
            return self._null_servo_position.get()

    @staticmethod
    def _get_correct_turn(turn: float):
        if turn < -1:
            turn = -1
        elif turn > 1:
            turn = 1
        return turn
