import struct

import utime
import ujson
from ..logging import getLogger
from ..controller import Startup

logger = getLogger('global_vars')

SYNC_CONFIG = 0
COMMUNICATION_ALLWAYS_SEND = 1
COMMUNICATION_REQUEST_SEND = 2
COMMUNICATION_RECV = 3

CHAR = 'c'
BOOL = 'b'
BYTE = 'b'
SHORT = 'h'
INT = 'i'
LONG = 'l'
FLOAT = 'f'
UNSIGNED_BYTE = 'B'
UNSIGNED_SHORT = 'H'

LENGTH_VARS = {
    CHAR: 1,
    BYTE: 1,
    UNSIGNED_BYTE: 1,
    SHORT: 2,
    UNSIGNED_SHORT: 2,
    INT: 4,
    FLOAT: 4,
}

FILENAME_CONFIG = 'global_vars.json'

AVAILABLE_PARAMS = (
    SYNC_CONFIG,
    COMMUNICATION_ALLWAYS_SEND,
    COMMUNICATION_REQUEST_SEND,
    COMMUNICATION_RECV
)
AVAILABLE_TYPES = (CHAR, BOOL, BYTE, SHORT, INT, LONG, FLOAT)


_vars = {}


class Var:
    _addr: bytes

    def __init__(self, addr: bytes, type_var=None, default_value=None, min_value=None, max_value=None, params=None):
        global _vars
        if len(addr) != 1:
            raise ValueError('addr має мати довжину 1 байт')
        if params is None:
            params = []

        is_new = addr not in _vars

        if not is_new and type_var is None:
            type_var = _vars[addr].type_var
        elif isinstance(type_var, str) and type_var in AVAILABLE_TYPES:
            pass
        elif type_var == bool:
            type_var = BOOL
        elif type_var == int:
            type_var = INT
        elif type_var == float:
            type_var = FLOAT
        else:
            raise ValueError(f'type_var={type_var} не підтримується')

        for param in params:
            if param not in AVAILABLE_PARAMS:
                raise ValueError(f'param={param} не підтримується')

        correct_value = self._check_value_with_type(type_var, default_value)
        correct_min_value = True if min_value is None else self._check_value_with_type(type_var, min_value)
        correct_max_value = True if max_value is None else self._check_value_with_type(type_var, max_value)

        if is_new:
            if correct_value and correct_min_value and correct_max_value:
                _vars[addr] = _LocalVar(type_var, default_value, min_value, max_value, list(params))
            else:
                raise ValueError(f'{(default_value, min_value, max_value)} не може існувати для type_var={type_var}')
        elif correct_min_value and correct_max_value:
            if min_value is not None and _vars[addr].min_value is None:
                _vars[addr].min_value = min_value
            if max_value is not None and _vars[addr].max_value is None:
                _vars[addr].max_value = max_value

            for param in params:
                if param not in _vars[addr].params:
                    _vars[addr].params.append(param)
        else:
            raise ValueError(f'Значення={(min_value, max_value)} не може існувати для type_var={type_var}')

        self._addr = addr

    def set(self, value):
        return self.addr_set(self._addr, value)

    def get(self):
        return self.addr_get(self._addr)

    def get_addr(self):
        return self._addr

    def get_last_update(self):
        return self.addr_last_update(self._addr)

    def get_type_var(self):
        return self.addr_get_type_var(self._addr)

    def get_length_type_var(self):
        return self.addr_get_length_type_var(self._addr)

    def get_params(self):
        return self.addr_get_params(self._addr)

    @classmethod
    def get_vars(cls, params):
        res = []
        for addr in _vars:
            is_add = True
            for param in params:
                if param not in _vars[addr].params:
                    is_add = False
                    break
            if is_add:
                res.append(cls(addr))
        return res

    @classmethod
    def addr_set(cls, addr, value):
        type_var = cls.addr_get_type_var(addr)
        if cls._check_value_with_type(type_var, value):
            if _vars[addr].min_value is None or value >= _vars[addr].min_value:
                if _vars[addr].max_value is None or value <= _vars[addr].max_value:
                    _vars[addr].value = value
                    _vars[addr].last_update = utime.ticks_ms()
                    if SYNC_CONFIG in _vars[addr].params:
                        config_file_save()
                    return True
        raise ValueError(f'value={value} не може існувати для type_var={type_var}')

    @staticmethod
    def addr_is_var(addr):
        return addr in _vars

    @staticmethod
    def addr_get(addr):
        return _vars[addr].value

    @staticmethod
    def addr_last_update(addr):
        return _vars[addr].last_update

    @staticmethod
    def addr_get_type_var(addr):
        return _vars[addr].type_var

    @staticmethod
    def addr_get_length_type_var(addr):
        return LENGTH_VARS[_vars[addr].type_var]

    @staticmethod
    def addr_get_params(addr):
        return _vars[addr].params

    @staticmethod
    def _check_value_with_type(type_var: str, value):
        try:
            struct.pack(type_var, value)
        except Exception:
            return False
        return True


class _LocalVar:
    type_var = None
    value = None
    min_value = None
    max_value = None
    params = list()
    last_update = 0

    def __init__(self, type_var, value, min_value, max_value, params):
        self.type_var = type_var
        self.value = value
        self.min_value = min_value
        self.max_value = max_value
        self.params = params
        self.last_update = utime.ticks_ms()


def config_file_load(controller):
    try:
        global _vars
        f = open(FILENAME_CONFIG, "r")
        values = ujson.load(f)
        f.close()
        for addr in values:
            try:
                _addr = bytes.fromhex(addr)
                var = Var(_addr)
                if SYNC_CONFIG in var.get_params():
                    var.set(values[addr])
            except Exception as e:
                logger.error(f'Error load var addr={addr}: {e}')
    except Exception as e:
        logger.error(f'Error read file')
    return True


def config_file_save():
    values = {}
    for addr in _vars:
        if SYNC_CONFIG in _vars[addr].params:
            values[addr.hex()] = _vars[addr].value
    f = open(FILENAME_CONFIG, "w")
    ujson.dump(values, f)
    f.close()


Startup(config_file_load)
