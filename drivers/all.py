"""
Тут буде драйвери для конкретних пристоїв, які використовуються у різних контролерах
"""
from machine import Pin, I2C
import utime

from .low_level import (
    DriverPWMServo,
    DriverLight,
    DriverMotor,
    DriverCollectorPWNMotor,
    DriverESCMotor,
    DriverEncoder,
    DriverDirectionEncoder,
    DriverBattery,
    DriverAccel,
    DriverGyro,
)
from controller import FREQ_NORMAL
from libs.mpu6050 import MPU6050 as _MPU6050


class ServoSG90(DriverPWMServo):
    """
    Драйвер для серви SG90
    """
    freq = 50
    duty_start = 1300
    duty_end = 8400
    max_angle = 180


class LEDLight(DriverLight):
    """
    Драйвер будь-якого LED світла.
    Яскравість змінюється через PWM
    """
    freq = 200


class CollectorMotor(DriverCollectorPWNMotor):
    """
    Драйвер для колекторних моторів.
    Напрямок руху керується через різні піни.
    Швидвість керується через PWM
    """
    freq = 100


class ESCBrushed1625(DriverESCMotor):
    """
    Драйвер для HobbyWing QuicRun WP 1625
    """
    freq = 50
    duty_start = 4000
    duty_end = 6000

    def _calibration(self):
        self.motor_value(1)
        utime.sleep(0.05)
        self.motor_value(0)


class Encoder(DriverEncoder):
    """
    Драйвер для енкодеру (для підрахунку відстані, кількості обертів за хв).
    Працює через кінцеві автомати.
    Без проблем визначає високу частоту імпульсів.
    """
    freq_update = FREQ_NORMAL


class DirectionEncoder(DriverDirectionEncoder):
    """
    Як звичайний енкодер, тільки з можливістю визначати напрямок руху.
    Підтримується енкодерами з двома контактами.
    Важливо! Контакти до яких підключено енкодер мають стояти поруч
    """
    freq_update = FREQ_NORMAL


class MPU6050(_MPU6050, DriverAccel, DriverGyro):
    """
    Драйвер для MPU6050 (акселерометр та гіроскоп)
    """
    def __init__(self, i2c_id: int, pin_sda: Pin, pin_scl: Pin, freq=400000):
        self._i2c = I2C(i2c_id, sda=pin_sda, scl=pin_scl, freq=freq)
        self._mpu = super().__init__(self._i2c)

    def get_accel_x(self):
        return self.accel.x

    def get_accel_y(self):
        return self.accel.y

    def get_accel_z(self):
        return self.accel.z

    def get_gyro_x(self):
        return self.gyro.x

    def get_gyro_y(self):
        return self.gyro.y

    def get_gyro_z(self):
        return self.gyro.z


class LiionBattery1s(DriverBattery):
    """
    Драйвер для визначення напруги та заряд акумулятора.
    Працює через дільник напруги (на резисторах).
    Налаштування для одної li-ion батареї.
    Налаштовано для +- адекватних значень при високих навантажені.
    Нажаль такому способу заміру заряду можна довіряти тільки приблизно.
    """
    min_voltage: float = 3.3
    max_voltage: float = 4.15
    smoothing1: float = 0.0005
    smoothing2: float = 0.04


class LiionBattery3s(DriverBattery):
    """
    Драйвер для визначення напруги та заряд акумулятора.
    Працює через дільник напруги (на резисторах).
    Налаштування для 3s li-ion батареї.
    Налаштовано для +- адекватних значень при високих навантажені.
    Нажаль такому способу заміру заряду можна довіряти тільки приблизно.
    """
    min_voltage: float = 9
    max_voltage: float = 12.3
    smoothing1: float = 0.0005
    smoothing2: float = 0.04
