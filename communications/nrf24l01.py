import struct
from .nrf24l01_lib import *
from machine import SPI, Pin
from ..config import config
from .base import Communication


class NRF24L01Communication(Communication):
    nrf: RF24
    buffer: None

    def __init__(self, spi_id: int, sck: Pin, mosi: Pin, miso: Pin, csn: Pin, ce: Pin):
        super().__init__()

        self.buffer = bytearray(32)

        send_pipe = b"\xd2\xf0\xf0\xf0\xf0"
        receive_pipe = b"\xe1\xf0\xf0\xf0\xf0"

        config.init_var('communication_nrf24l01_channel', int, 1, min_value=1, max_value=125)

        self.nrf = RF24(
            spi=SPI(1, sck=Pin(10), mosi=Pin(11), miso=Pin(12)),
            csn=csn,
            ce_pin=ce,
            )
        
        self.nrf.ack = True
        self.nrf.pa_level = -12
        self.nrf.data_rate = 250

        self.nrf.open_tx_pipe(send_pipe)
        self.nrf.open_rx_pipe(1, receive_pipe)

        self.nrf.channel = config.communication_nrf24l01_channel
        self.nrf.dynamic_payloads = False
        self.nrf.payload_length = 8

        self.nrf.listen = True
        self.nrf.load_ack(self.buffer[:self.nrf.payload_length], 1)

 
    def recv(self):
        while True:
            if self.nrf.available():
                package = self.nrf.read()
                t, m, l = struct.unpack("bbb", package)
                t = t / 100
                m = m / 100
                l = 3 if l else 0
                if m > 0:
                    a = m
                    r = 0
                else:
                    a = 0
                    r = -m
                data = {
                    't': t,
                    'a': a,
                    'r': r,
                    'l': l,
                }
                self.nrf.load_ack(self.buffer[:self.nrf.payload_length], 1)
                return data
 
    def send(self, data):
        self.buffer = struct.pack(
            "BBhi",
            int(data['battery_percent']),
            int(data['battery_voltage']*10),
            int(data['speed']*10),
            int(data['mileage']*10),
        )
