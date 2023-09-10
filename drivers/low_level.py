"""
Тут буде базова логіка для адаптерів різних пристроїв
"""
import machine
import rp2
import utime

from controller import FREQ_SLOW, FREQ_NORMAL, FREQ_FAST
from .base import BaseDriver
from machine import Pin, PWM, ADC


class DriverPWMServo(BaseDriver):
    freq: int
    duty_start: int
    duty_end: int
    max_angle: float

    _pin: Pin
    _pwm: PWM
    _angle: float = -1
    _start_angle: float

    def __init__(self, pin: Pin, start_angle=0) -> None:
        super().__init__()
        self._pin = pin
        self._start_angle = start_angle

    def set_position(self, position: float):
        if position < 0:
            position = 0
        elif position > 1:
            position = 1

        angle = position * self.max_angle
        self.set_angle(angle)

    def set_angle(self, angle: float):
        angle = self._get_correct_angle(angle)
        if angle != self._angle:
            duty = self._get_duty(angle)
            self._angle = angle
            self._pwm.duty_u16(duty)
        return True

    def _startup(self, controller):
        self._pwm = PWM(self._pin)
        self._pwm.freq(self.freq)
        self.set_angle(self._start_angle)

    def _shutdown(self, controller):
        self._pwm.deinit()
    
    def _get_correct_angle(self, angle: float):
        if angle < 0:
            angle = 0
        elif angle > self.max_angle:
            angle = self.max_angle
        return angle
    
    def _get_duty(self, angle):
        _kangle = angle / self.max_angle
        duty = self.duty_start + _kangle*(self.duty_end - self.duty_start)
        return int(duty)


class DriverLight(BaseDriver):
    freq: int

    _pin: Pin
    _pwm: PWM
    _intensity: float
    _old_intensity: float = -1
    _start_intensity: float = 0

    def __init__(self, pin: Pin, start_intensity=0) -> None:
        super().__init__()
        self._pin = pin
        self._start_intensity = start_intensity

    def set_intensity(self, intensity: float):
        intensity = self._get_correct_intensity(intensity)
        if self._old_intensity == intensity:
            return
        self._intensity = intensity
        duty = int(intensity * 255 * 255)
        self._pwm.duty_u16(duty)
        self._old_intensity = intensity

    def _startup(self, controller):
        self._pwm = PWM(self._pin)
        self._pwm.freq(self.freq)
        self.set_intensity(self._start_intensity)

    def _shutdown(self, controller):
        self._pwm.deinit()

    @staticmethod
    def _get_correct_intensity(intensity: float):
        if intensity < 0:
            intensity = 0
        elif intensity > 1:
            intensity = 1
        return intensity


class DriverMotor(BaseDriver):
    freq: int

    _motor_value: float = 0

    def motor_value(self, motor_value: float):
        pass

    @staticmethod
    def _get_correct_motor_value(motor_value: float):
        if motor_value < -1:
            motor_value = -1
        elif motor_value > 1:
            motor_value = 1
        return motor_value


class DriverCollectorPWNMotor(DriverMotor):
    freq: int

    _pin_forward: Pin
    _pin_back: Pin
    _pin_speed: Pin
    _pwm_forward: PWM
    _pwm_back: PWM
    _pwm_speed: PWM
    _motor_value: float = 0

    def __init__(self, pin_forward: Pin, pin_back: Pin, pin_speed: Pin = None):
        super().__init__()
        self._pin_forward = pin_forward
        self._pin_back = pin_back
        self._pin_speed = pin_speed

    def _startup(self, controller):
        if self._pin_speed:
            self._pwm_speed = PWM(self._pin_speed)
            self._pwm_speed.freq(self.freq)
            self._pin_forward.value(0)
            self._pin_back.value(0)
        else:
            self._pwm_forward = PWM(self._pin_forward)
            self._pwm_forward.freq(self.freq)
            self._pwm_back = PWM(self._pin_back)
            self._pwm_back.freq(self.freq)

    def _shutdown(self, controller):
        if self._pwm_speed:
            self._pwm_speed.deinit()
        self._pwm_forward.deinit()
        self._pwm_back.deinit()

    def motor_value(self, motor_value: float):
        _motor_value = self._get_correct_motor_value(motor_value)
        if _motor_value != self._motor_value:
            if _motor_value >= 0:
                duty = self._get_duty(_motor_value)
                if self._pwm_speed:
                    self._pwm_speed.duty_u16(duty)
                    self._pin_forward.value(1)
                    self._pin_back.value(0)
                else:
                    self._pwm_forward.duty_u16(duty)
                    self._pwm_back.duty_u16(0)
            else:
                duty = self._get_duty(-_motor_value)
                if self._pwm_speed:
                    self._pwm_speed.duty_u16(duty)
                    self._pin_forward.value(0)
                    self._pin_back.value(1)
                else:
                    self._pwm_back.duty_u16(duty)
                    self._pwm_forward.duty_u16(0)
            self._motor_value = motor_value

    @staticmethod
    def _get_duty(value):
        duty = 65025 * value
        return int(duty)


class DriverESCMotor(DriverMotor):
    freq: int
    duty_start: int
    duty_end: int

    _pin: Pin
    _pwm: PWM

    def __init__(self, pin: Pin) -> None:
        super().__init__()
        self._pin = pin

    def motor_value(self, value: float):
        value = self._get_correct_motor_value(value)
        if value != self._motor_value:
            duty = self._get_duty(value)
            self._motor_value = value
            self._pwm.duty_u16(duty)
        return True

    def _calibration(self):
        pass

    def _startup(self, controller):
        self._pwm = PWM(self._pin)
        self._pwm.freq(self.freq)
        self._calibration()

    def _shutdown(self, controller):
        self._pwm.deinit()

    def _get_duty(self, value):
        _kangle = (value + 1) / 2
        duty = self.duty_start + _kangle * (self.duty_end - self.duty_start)
        return int(duty)


class DriverEncoder(DriverMotor):
    freq_update = 1000000

    _pin0: Pin
    _count_pulses_rotation: int
    _sm_count: rp2.StateMachine
    _rpm: int = 0
    _rotation_count: float = 0
    _old_count: int = 0
    _old_count_time = utime.ticks_cpu()
    _time_diff = 1

    def __init__(self, pin0: Pin, count_pulses_rotation: int):
        super().__init__()
        self._pin0 = pin0
        self._count_pulses_rotation = count_pulses_rotation

    def get_rpm(self):
        return self._rpm

    def get_rotation_count(self):
        return self._rotation_count

    def _startup(self, controller):
        self._sm_count = rp2.StateMachine(0, self.__count, in_base=self._pin0)
        self._sm_count.active(1)

    def _update(self, controller):
        count_sm = 0
        print(self._sm_count.rx_fifo(), count_sm)
        for _ in range(self._sm_count.rx_fifo()):
            count_sm = self._sm_count.get()
        print(self._sm_count.rx_fifo(), count_sm)
        for _ in range(self._sm_count.rx_fifo()):
            count_sm = self._sm_count.get()
        print(self._sm_count.rx_fifo(), count_sm)
        for _ in range(self._sm_count.rx_fifo()):
            count_sm = self._sm_count.get()
        print(self._sm_count.rx_fifo(), count_sm)
        # self._calc_rpm(count_sm)

    def _calc_rpm(self, count_sm):
        if count_sm > self._old_count:
            self._old_count = count_sm
            return 0
        if count_sm <= 1:
            count_sm = self._old_count

        rotation_count = (self._old_count - count_sm) / self._count_pulses_rotation
        self._rotation_count += rotation_count
        self._time_diff = utime.ticks_diff(utime.ticks_cpu(), self._old_count_time)
        self._rpm = int(rotation_count * (1000000 / self._time_diff) * 60)
        print(self._old_count - count_sm, self._time_diff, self._rpm)
        self._old_count = count_sm
        self._old_count_time = utime.ticks_cpu()

    @staticmethod
    def _get_sm_last_value(sm, default=0):
        for _ in range(sm.rx_fifo()):
            default = sm.get()
        return default

    @staticmethod
    @rp2.asm_pio()
    def __count():
        set(x, 0)
        wrap_target()

        wait(1, pin, 0)
        jmp(x_dec, 'd0')
        label('d0')
        mov(isr, x)
        push(iffull,noblock)

        wait(0, pin, 0)
        jmp(x_dec, 'd1')
        label('d1')
        mov(isr, x)
        push(iffull,noblock)
        
        wrap()


class DriverDirectionEncoder(DriverEncoder):
    _pin1: Pin
    _invert_direction: bool
    _sm_direction: rp2.StateMachine
    _direction: int = 0

    def __init__(self, pin0: Pin, pin1: Pin, count_pulses_rotation: int, invert_direction: bool = False):
        super().__init__(pin0, count_pulses_rotation)
        self._pin1 = pin1
        self._invert_direction = invert_direction

    def get_direction(self):
        return self._direction

    def _startup(self, controller):
        super()._startup(controller)
        self._sm_direction = rp2.StateMachine(1, self.__direction, in_base=self._pin0)
        self._sm_direction.active(1)

    def _update(self, controller):
        super()._update(controller)

        direction = self._get_sm_last_value(self._sm_direction, 0)
        self._direction = self._calc_direction(direction)

    def _calc_direction(self, direction_sm):
        direction = self._direction
        if direction_sm == 2:
            direction = 1
        elif direction_sm == 1:
            direction = -1
        if self._invert_direction:
            direction = -direction 
        return direction

    @staticmethod
    @rp2.asm_pio()
    def __count():
        set(osr, 0)
        wrap_target()
        label('loop')

        in_(pins, 2)
        mov(x, isr)
        mov(isr, osr)
        push(noblock)
        jmp(x_not_y, 'ok')
        jmp('loop')

        label('ok')
        mov(y, x)
        mov(x, osr)
        jmp(x_dec, 'd1')
        label('d1')
        mov(osr, x)
        jmp('loop')

        wrap()

    @staticmethod
    @rp2.asm_pio()
    def __direction():
        wrap_target()
        label('loop')
        in_(pins, 2)
        mov(x, isr)
        jmp(not_x, 'direction')
        jmp('loop')


        label('direction')
        in_(pins, 2)
        mov(x, isr)
        jmp(not_x, 'direction')
        push(noblock)
        jmp('loop')
        wrap()


class DriverBattery(BaseDriver):
    freq_update = FREQ_SLOW

    min_voltage: float
    max_voltage: float
    smoothing1: float
    smoothing2: float

    _pin_battery_adc: Pin
    _pin_charge: Pin
    _r1: int
    _r2: int
    _rdel: float
    _adc_battery: ADC
    _voltage: float = 0
    _percent: float = 0

    def __init__(
            self,
            pin_battery_adc: Pin,
            pin_charge: Pin = None,  # type: ignore
            r1: int = 1000000,
            r2: int = 100000,
            ):
        super().__init__()
        self._pin_battery_adc = pin_battery_adc
        self._pin_charge = pin_charge
        self._r1 = r1
        self._r2 = r2
        self._rdel = r2/(r1+r2)

    def get_voltage(self):
        return round(self._voltage, 2)

    def get_percent(self):
        return self._percent

    def get_current_voltage(self):
        u16 = self._adc_battery.read_u16()
        voltage = u16 / 65535 * 3.3
        voltage_battery = voltage / self._rdel
        return voltage_battery

    def _startup(self, controller):
        self._adc_battery = ADC(self._pin_battery_adc)

    def _update(self, controller):
        current_voltage = self.get_current_voltage()
        if self._voltage <= 0:
            self._voltage = current_voltage
        else:
            smoothing = self.smoothing1
            if current_voltage > self._voltage:
                smoothing = self.smoothing2
            self._voltage -= smoothing * (self._voltage - current_voltage)

        percent = int(((self._voltage - self.min_voltage) / (self.max_voltage - self.min_voltage)) * 10) * 10
        if percent < 0:
            percent = 0
        elif percent > 100:
            percent = 100
        self._percent = percent


class DriverAccel(BaseDriver):
    """
    Базовий драйвер для читання значень акселерометра
    """

    def get_accel_x(self) -> float:
        pass

    def get_accel_y(self) -> float:
        pass

    def get_accel_z(self) -> float:
        pass


class DriverGyro(BaseDriver):
    """
    Базовий драйвер для читання значень гіроскопа
    """

    def get_gyro_x(self) -> float:
        pass

    def get_gyro_y(self) -> float:
        pass

    def get_gyro_z(self) -> float:
        pass
