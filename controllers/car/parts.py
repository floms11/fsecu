import utime
import math
from ...config import config
from ...loop import Loop, FREQ_NORMAL
from ...drivers import DriverPWMServo, DriverMotor, DriverEncoder, DriverDirectionEncoder, DriverLight

LIGHT_VALUE_OFF = 0 # Світло вимкнено
LIGHT_VALUE_DRL = 1 # Увімкнено тільки денні ходові вогні
LIGHT_VALUE_ON = 2 # Ближнє світло увімкнено
LIGHT_VALUE_FULL = 3 # Дальнє світло увімкнено


class Turn:
    """
    Модуль для керування поворотами.
    Використовується для класичного транспорту з єдиною поворотною вісю
    """
    _servo: DriverPWMServo
    _turn: float = 0
    _degrees_second: int = 0
    _speed_coefficient: float = 0
    _turn_coefficient: float = 0

    def __init__(
            self,
            servo: DriverPWMServo,
            ) -> None:
        self._servo = servo

        config.init_var('turn_left_servo_position', float, 0, 0, 1)
        config.init_var('turn_null_servo_position', float, 0.5, 0, 1)
        config.init_var('turn_right_servo_position', float, 1, 0, 1)
        config.init_var('turn_quadratic_controll', bool, True)
        
        Loop(callback=self._update, freq=FREQ_NORMAL)
    
    def set(self, turn: float):
        self._turn = self._get_correct_turn(turn)
    
    def set_degrees_second(self, degrees):
        self._degrees_second = degrees
    
    def set_speed_coefficient(self, speed_coefficient):
        self._speed_coefficient = speed_coefficient
    
    def _update(self):
        turn = self._turn
        if config.turn_quadratic_controll:
            turn = self._get_quadratic_value(turn)
        
        # Поки у форматі милиці
        if turn == 0 and self._degrees_second != 0 and self._speed_coefficient > 0:
            _vc = self._degrees_second/250
            direction = 1 if _vc >= 0 else -1
            _vc = abs(_vc)
            _v = (_vc**(1/2) / (1 + 2*self._speed_coefficient))
            # _v = (_vc**(1/9) / 6)
            # _v += _vc ** 1.5
            if _v > 1:
                _v = 1
            elif _v < 0:
                _v = 0
            self._turn_coefficient = _v * direction
            self._degrees_second = 0
        elif turn != 0 or self._speed_coefficient <= 0:
            self._turn_coefficient = 0
        
        position = self._get_turn_servo_position(turn + self._turn_coefficient)
        self._servo.set_position(position)
    
    @staticmethod
    def _get_quadratic_value(value):
        turn_d = 1 if value >= 0 else -1
        return (value ** 2) * turn_d
    
    def _get_turn_servo_position(self, turn) -> float:
        if turn < 0:
            _turn = -turn
            position = config.turn_left_servo_position*(_turn) + (config.turn_null_servo_position)*(1-_turn)
            return position
        elif turn > 0:
            _turn = turn
            position = config.turn_right_servo_position*(_turn) + (config.turn_null_servo_position)*(1-_turn)
            return position
        else:
            return config.turn_null_servo_position
    
    def _get_correct_turn(self, turn: float):
        if turn < -1:
            turn = -1
        elif turn > 1:
            turn = 1
        return turn


class Move:
    """
    Модуль для керування рухом.
    Використовується для транспорту з єдиним мотором
    """
    _motor: DriverMotor
    _motor_encoder: DriverEncoder

    _acceleration: float = 0
    _revers: float = 0
    _brake: float = 0
    _handbrake: bool = False
    
    _speed_kmh: float = 0
    _speed_coefficient: float = 0
    _last_update: int = 0

    def __init__(
            self, 
            motor: DriverMotor,
            motor_encoder: DriverEncoder = None, # type: ignore
            ) -> None:
        self._motor = motor
        self._motor_encoder = motor_encoder

        config.init_var('motor_max_rpm', int, 0, 0, 100000)
        config.init_var('motor_start_value', float, 0, 0, 1)
        config.init_var('move_quadratic_controll', bool, True)
        config.init_var('move_delay_controll', int, 100, 10, 10000)

        Loop(callback=self._update, freq=FREQ_NORMAL)

    
    def set(self, acceleration: float, revers: float, brake: float, handbrake: bool):
        self._acceleration = self._get_value(acceleration)
        self._revers = self._get_value(revers)
        self._brake = self._get_value(brake)
        self._handbrake = handbrake
        self._last_update = utime.ticks_ms()
    
    def get_speed(self, is_coefficient: bool = False):
        return round(self._speed_coefficient if is_coefficient else self._speed_kmh, 2)
    

    def _update(self):
        if utime.ticks_diff(utime.ticks_ms(), self._last_update) > config.move_delay_controll:
            to_motor_value = 0
        else:
            to_motor_value = self._acceleration - self._revers

        if config.move_quadratic_controll:
            to_motor_value = self._get_quadratic_value(to_motor_value)

        # Якщо є енкодер, рахуємо motor_value з урахуванням обертів
        if False: # self.motor_encoder and config.motor_max_rpm > 0:
            if to_motor_value != 0:
                motor_direction = 1 if to_motor_value > 0 else -1
                motor_value_no_direction = abs(to_motor_value)

                max_motor_value = config.motor_start_value + (1-config.motor_start_value)*motor_value_no_direction
                current_rpm = self.motor_encoder.get_rpm()
                to_rpm = motor_value_no_direction * config.motor_max_rpm
                
                if to_rpm > current_rpm:
                    to_motor_value = 1 - current_rpm / to_rpm
                    if to_motor_value > max_motor_value:
                        to_motor_value = max_motor_value
                else:
                    to_motor_value = 0
                if to_motor_value < motor_value_no_direction:
                    to_motor_value = motor_value_no_direction
                to_motor_value = to_motor_value * motor_direction

        self._motor.motor_value(to_motor_value)

        # Рахуємо швидкість
        if self.motor_encoder:
            wheel_length = config.wheel_radius * 2 * math.pi * 0.001 # Довжина колеса у метрах
            rpm = self.motor_encoder.get_rpm()
            rpm_wheel = rpm / config.gear_ratio
            # Швидкість в км/г
            self._speed_kmh = rpm_wheel * 60 * wheel_length * 0.001
            # Коефіцієнт швидкості
            speed_coefficient = rpm / config.motor_max_rpm
            if speed_coefficient < 0:
                speed_coefficient = 0
            elif speed_coefficient > 1:
                speed_coefficient = 1
            self._speed_coefficient = speed_coefficient
    
    @staticmethod
    def _get_quadratic_value(value):
        turn_d = 1 if value >= 0 else -1
        return (value ** 2) * turn_d

    @staticmethod
    def _get_value(value):
        if value < 0:
            return 0
        elif value > 1:
            return 1
        else:
            return value
    
    @property
    def motor_encoder(self):
        return self._motor_encoder


class Light:
    """
    Модуль для керування світлом.
    Достатньо простий модуль який підримує переднє/заднє світло та варіації ближнього/дальнього
    """
    front_light: DriverLight
    back_light: DriverLight

    def __init__(self, front_light: DriverLight, back_light: DriverLight) -> None:
        self.front_light = front_light
        self.back_light = back_light

        config.init_var('light_normal_intensity', float, 0.5, 0, 1)

        self.set(LIGHT_VALUE_OFF)
    
    def set(self, value: int = LIGHT_VALUE_OFF, front_full: bool = False, back_full: bool = False):
        front = 0
        back = 0
        if value == LIGHT_VALUE_DRL:
            front = config.light_normal_intensity
            back = 0
        elif value == LIGHT_VALUE_ON:
            front = config.light_normal_intensity
            back = config.light_normal_intensity
        elif value == LIGHT_VALUE_FULL:
            front = 1
            back = config.light_normal_intensity

        if front_full:
            front = 1
        if back_full:
            back = 1
        self.front_light.set_intensity(front)
        self.back_light.set_intensity(back)
