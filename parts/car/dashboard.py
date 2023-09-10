import math
import utime
from ..base import BasePart
from global_vars import Var, SHORT, BYTE, SYNC_CONFIG, COMMUNICATION_ALLWAYS_SEND
from drivers import DriverEncoder, DriverBattery
from controller import Controller, FREQ_MEDIUM


class Dashboard(BasePart):
    freq_update = FREQ_MEDIUM
    thread = True

    _motor_encoder: DriverEncoder
    _battery: DriverBattery

    _period_write_mileage: int = 1000  # ms
    _filename_mileage: str = '.mileage'

    _wheel_radius = Var(b'\xf0', float, 0, params=(SYNC_CONFIG, ))
    _gear_ratio = Var(b'\xf1', float, 0, params=(SYNC_CONFIG, ))
    _motor_max_rpm = Var(b'\xf2', float, 0, params=(SYNC_CONFIG, ))

    _mileage_var = Var(b'\xb0', float, 0, params=(COMMUNICATION_ALLWAYS_SEND, ))
    _speed_var = Var(b'\xb1', SHORT, 0, params=(COMMUNICATION_ALLWAYS_SEND, ))
    _battery_percent_var = Var(b'\xb2', BYTE, 0, params=(COMMUNICATION_ALLWAYS_SEND, ))
    _battery_voltage_var = Var(b'\xb3', BYTE, 0, params=(COMMUNICATION_ALLWAYS_SEND, ))

    _mileage: float = 0
    _mileage_rotation_count: float = 0
    _speed_kmh: float = 0
    _speed_coefficient: float = 0
    _last_write_mileage: int = 0

    def __init__(
            self,
            motor_encoder: DriverEncoder = None,
            battery: DriverBattery = None,
    ) -> None:
        super().__init__()
        self._motor_encoder = motor_encoder
        self._battery = battery

    def get_speed(self, is_coefficient: bool = False):
        return round(self._speed_coefficient if is_coefficient else self._speed_kmh, 2)

    def get_mileage(self):
        return round(self._mileage, 2)

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

    def _startup(self, controller: Controller):
        self._read_mileage()

    def _update(self, controller: Controller):
        if self._motor_encoder:
            # Швидкість
            wheel_length = self._wheel_radius.get() * 2 * math.pi * 0.001  # Довжина колеса у метрах
            rpm = self._motor_encoder.get_rpm()
            rpm_wheel = rpm / self._gear_ratio.get()
            # Швидкість в км/г
            self._speed_kmh = rpm_wheel * 60 * wheel_length * 0.001
            # Коефіцієнт швидкості
            speed_coefficient = rpm / self._motor_max_rpm.get()
            if speed_coefficient < 0:
                speed_coefficient = 0
            elif speed_coefficient > 1:
                speed_coefficient = 1
            self._speed_coefficient = speed_coefficient

            # Пробіг
            rotation_count_motor = self._motor_encoder.get_rotation_count()
            rotation_count_motor_iteration = rotation_count_motor - self._mileage_rotation_count
            rotation_count = rotation_count_motor_iteration / self._gear_ratio.get()
            distance = rotation_count * wheel_length
            self._mileage += distance
            self._mileage_rotation_count = rotation_count_motor
            self._write_mileage()

        self._set_vars()

    def _set_vars(self):
        self._mileage_var.set(self.get_mileage())
        self._speed_var.set(int(self.get_speed()*10))
        self._battery_percent_var.set(int(self.get_battery_percent()))
        self._battery_voltage_var.set(int(self.get_battery_voltage() * 10))

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
