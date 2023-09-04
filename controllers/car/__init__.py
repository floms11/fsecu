import utime
import math
import _thread
from ...loop import Loop, start, FREQ_NORMAL, FREQ_MEDIUM
from ...drivers import DriverAccel, DriverGyro, DriverBattery
from ...communications import Communication
from ...config import config
from .parts import *


class CarController:
    """
    Контролер для керування класичним транспортом з одним потором та єдиною поворотною вісю.
    Контролер модульний. Підлаштовується під налаштовані модулі.
    Після визначення викликається метод start(), він починає нескінченний цикл керування транспортом
    """
    _turn: Turn
    _move: Move
    _communication: Communication
    _light: Light
    _battery: DriverBattery
    _accel: DriverAccel
    _gyro: DriverGyro
    _communication_is_send_data: bool = True

    _period_send_data: int = 50 # ms
    _period_write_mileage: int = 1000 # ms
    _filename_mileage: str = '.mileage'


    _communication_turn: float = 0
    _communication_acceleration: float = 0
    _communication_revers: float = 0
    _communication_brake: float = 0
    _communication_handbrake: bool = False
    _communication_light_full_front: bool = False
    _communication_light: int = LIGHT_VALUE_OFF
    _communication_last_update: int = 0
    _mileage: float = 0
    _last_send_data: int = 0
    _last_rotation_count: float = 0
    _last_write_mileage: int = 0
    _is_start: bool = False

    def __init__(
            self,
            turn: Turn,
            move: Move, 
            communication: Communication,
            light: Light = None, # type: ignore
            battery: DriverBattery = None, # type: ignore
            accel: DriverAccel = None, # type: ignore
            gyro: DriverGyro = None, # type: ignore
            ) -> None:
        self._turn = turn
        self._move = move
        self._communication = communication
        self._light = light
        self._battery = battery
        self._accel = accel
        self._gyro = gyro

        config.init_var('gear_ratio', float, 0, 0, 50)
        config.init_var('wheel_radius', float, 0, 0, 200)
    
    def thread_communication(self):
        while True:
            self._update_communication()
            self._update_controlls()
    
    def start(self):
        if self._is_start:
            raise Exception('CarController: Контролер вже запущено')
        self._is_start = True
        
        if config.gear_ratio > 0 and config.wheel_radius > 0 and self._move.motor_encoder:
            self._read_mileage()
            Loop(callback=self._update_speed_and_mileage, freq=FREQ_NORMAL)
        if self._accel:
            Loop(callback=self._update_accel, freq=FREQ_NORMAL)
        if self._gyro:
            Loop(callback=self._update_gyro, freq=FREQ_NORMAL)

        _thread.start_new_thread(self.thread_communication, ())
        print('CarController: Успішно визначено для керування')
        start()

    
    def get_speed(self, is_coefficient: bool = False):
        return self._move.get_speed(is_coefficient)
    
    def get_motor_rpm(self):
        rpm = 0
        if self._move.motor_encoder:
            rpm = self._move.motor_encoder.get_rpm()
        return rpm
    
    def get_motor_direction(self):
        direction = 0
        if isinstance(self._move.motor_encoder, DriverDirectionEncoder):
            direction = self._move.motor_encoder.get_direction()
        return direction
    
    def get_battery_percent(self):
        percent = 0
        if self._battery:
            percent = self._battery.get_percent()
        return percent
    
    def get_battery_voltage(self):
        voltage = 0
        if self._battery:
            voltage = self._battery.get_voltage()
        return voltage
    
    def get_mileage(self):
        return round(self._mileage, 2)

    def _read_mileage(self):
        try:
            f = open(self._filename_mileage, "r")
            self._mileage = float(f.read())
            f.close()
        except:
            pass

    def _write_mileage(self):
        t = utime.ticks_ms()
        if utime.ticks_diff(t, self._last_write_mileage) > self._period_write_mileage:
            try:
                f = open(self._filename_mileage, "w")
                f.write(str(self._mileage))
                f.close()
            except:
                pass
            self._last_write_mileage = t

    def _update_communication(self):
        request = self._communication.recv()
        if request:
            self._communication_send()
            if 't' in request:
                self._communication_turn = request['t']
            if 'a' in request:
                self._communication_acceleration = request['a']
            if 'r' in request:
                self._communication_revers = request['r']
            if 'b' in request:
                self._communication_brake = request['b']
            if 'h' in request:
                self._communication_handbrake = bool(request['h'])
            if 'l' in request:
                self._communication_light = request['l']
            if 'L' in request:
                self._communication_light_full_front = bool(request['L'])
            self._communication_last_update = utime.ticks_ms()
    
    def _update_controlls(self):
        self._turn.set(self._communication_turn)
        self._move.set(
            acceleration=self._communication_acceleration,
            revers=self._communication_revers,
            brake=self._communication_brake,
            handbrake=self._communication_handbrake,
        )
        if self._light:
            self._light.set(self._communication_light, front_full=self._communication_light_full_front)

    def _update_speed_and_mileage(self):
        encoder = self._move.motor_encoder
        wheel_length = config.wheel_radius * 2 * math.pi * 0.001 # Довжина колеса у метрах

        # Пробіг в метрах
        rotation_count_motor = encoder.get_rotation_count()
        rotation_count_motor_iteration = rotation_count_motor - self._last_rotation_count
        rotation_count = rotation_count_motor_iteration / config.gear_ratio
        distance = rotation_count * wheel_length
        self._mileage += distance
        self._last_rotation_count = rotation_count_motor
        self._write_mileage()

        # Поки трішки милиця
        speed_coefficient = self.get_speed(True)
        self._turn.set_speed_coefficient(speed_coefficient)

    def _update_accel(self):
        pass

    def _update_gyro(self):
        # Поки трішки милиця
        if isinstance(self._move.motor_encoder, DriverDirectionEncoder):
            direction = self._move.motor_encoder.get_direction()
            self._turn.set_degrees_second(direction * self._gyro.get_gyro_z())

    def _communication_send(self):
        if self._communication_is_send_data:
            t = utime.ticks_ms()
            if utime.ticks_diff(t, self._last_send_data) > self._period_send_data:
                data_send = {
                    'speed': self.get_speed(),
                    'mileage': self.get_mileage(),
                    'motor_direction': self.get_motor_direction(),
                    'motor_rpm': self.get_motor_rpm(),
                    'battery_percent': self.get_battery_percent(),
                    'battery_voltage': self.get_battery_voltage(),
                }
                self._communication.send(data_send)
                self._last_send_data = t
