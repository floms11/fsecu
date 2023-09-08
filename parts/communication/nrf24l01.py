import struct

import utime

from ...controller import FREQ_FAST, Controller
from ...libs.nrf24l01 import *
from machine import SPI, Pin
from ..base import BasePart
from ...global_vars import Var, SYNC_CONFIG, COMMUNICATION_ALLWAYS_SEND, COMMUNICATION_REQUEST_SEND, COMMUNICATION_RECV
from ...logging import getLogger

logger = getLogger('nrf21l01')


class NRF24L01Communication(BasePart):
    freq_update = FREQ_FAST
    thread = True
    nrf: RF24

    _channel = Var(b'\xe0', int, 1, 0, 125, params=(SYNC_CONFIG, ))
    _pipe = Var(b'\xe1', int, 1000, params=(SYNC_CONFIG, ))
    _pa_level = Var(b'\xe2', int, 0, params=(SYNC_CONFIG, ))
    _data_rate = Var(b'\xe3', int, 0, params=(SYNC_CONFIG, ))

    def __init__(self, spi_id: int, sck: Pin, mosi: Pin, miso: Pin, csn: Pin, ce: Pin):
        super().__init__()

        self._spi_id = spi_id
        self._sck = sck
        self._mosi = mosi
        self._miso = miso
        self._csn = csn
        self._ce = ce
        self._buffer = bytearray(32)

    def _startup(self, controller: Controller):
        send_pipe = b"\xa1" + self._pipe.get().to_bytes(4, 'big')
        receive_pipe = b"\xb1" + self._pipe.get().to_bytes(4, 'big')

        self.nrf = RF24(
            spi=SPI(self._spi_id, sck=self._sck, mosi=self._mosi, miso=self._miso),
            csn=self._csn,
            ce_pin=self._ce,
            )

        self.nrf.ack = True
        self.nrf.pa_level = self._pa_level.get()
        self.nrf.data_rate = self._data_rate.get()

        self.nrf.open_tx_pipe(send_pipe)
        self.nrf.open_rx_pipe(1, receive_pipe)

        self.nrf.channel = self._channel.get()
        self.nrf.dynamic_payloads = False
        self.nrf.payload_length = 8

        self.nrf.listen = True
        self.nrf.load_ack(self._buffer[:self.nrf.payload_length], 1)

        vars_send = Var.get_vars([COMMUNICATION_ALLWAYS_SEND])
        self.vars_send = {var.get_addr(): utime.ticks_ms() for var in vars_send}
        self.vars_request = []

    def _update(self, controller: Controller):
        if self.nrf.available():
            package = self.nrf.read()
            self._recv_update(package)
            self._send_update()

    def _recv_update(self, package):
        s = 0
        fmt = '<'
        while s < self.nrf.payload_length:
            addr = package[s].to_bytes(1, 'big')
            if addr == b'\xfe':
                fmt += f"bb"
                s += 1
            elif addr != b'\x00':
                type_var = Var.addr_get_type_var(addr)
                length = Var.addr_get_length_type_var(addr)
                fmt += f"b{type_var}"
                s += length
            s += 1
        values = struct.unpack(fmt, package)
        for i in range(0, len(values), 2):
            addr = values[i].to_bytes(1, 'big')
            value = values[i+1]
            if addr == b'\xfe':
                if Var.addr_is_var(value.to_bytes(1, 'big')) and COMMUNICATION_REQUEST_SEND in Var.addr_get_params(value.to_bytes(1, 'big')):
                    self.vars_request.append(value.to_bytes(1, 'big'))
            elif Var.addr_is_var(addr) and COMMUNICATION_RECV in Var.addr_get_params(addr):
                Var.addr_set(addr, value)

    def _send_update(self):
        items = list(self.vars_send.items())
        for var in self.vars_request:
            if var not in self.vars_send:
                items.append((var, 0))
        vars_send = sorted(items, key=lambda item: item[1])
        payload_length = 0
        fmt = '<'
        send = []
        for addr, time_update in vars_send:
            new_payload_length = payload_length + Var.addr_get_length_type_var(addr) + 1
            if new_payload_length <= self.nrf.payload_length:
                fmt += f"b{Var.addr_get_type_var(addr)}"
                send.append(int.from_bytes(addr, 'big'))
                send.append(Var.addr_get(addr))
                self.vars_send[addr] = utime.ticks_ms()
                payload_length = new_payload_length
            else:
                break
        self._buffer = struct.pack(fmt, *send)
        self._buffer = self._buffer + (self.nrf.payload_length - len(self._buffer)) * b'\x00'
        self.nrf.load_ack(self._buffer[:self.nrf.payload_length], 1)
        self.vars_request = []
