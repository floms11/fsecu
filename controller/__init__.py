import _thread

import utime

from parts.base import BasePart
from logging import getLogger


FREQ_VERY_FAST = 100
FREQ_FAST = 1000
FREQ_NORMAL = 10000
FREQ_MEDIUM = 50000
FREQ_SLOW = 100000
FREQ_VERY_SLOW = 1000000


_updates = []
_startups = []
_shutdowns = []

_updates_thread = []
_startups_thread = []
_shutdowns_thread = []


class Update:
    callback = None
    freq = None

    def __init__(self, callback, freq=FREQ_NORMAL, thread=False):
        self.callback = callback
        self.freq = freq
        if thread:
            _updates_thread.append(self)
        else:
            _updates.append(self)


class Startup:
    function = None

    def __init__(self, function, thread=False):
        self.function = function
        if thread:
            _startups_thread.append(self)
        else:
            _startups.append(self)


class Shutdown:
    function = None

    def __init__(self, function, thread=False):
        self.function = function
        if thread:
            _shutdowns_thread.append(self)
        else:
            _shutdowns.append(self)


class Controller:
    _parts = tuple()
    _is_update = False
    _started_thread0 = False

    def __init__(self, *parts):
        parts_ok = []
        types_ok = []

        for part in parts:
            if isinstance(part, BasePart):
                if type(part) not in types_ok:
                    parts_ok.append(part)
                    types_ok.append(type(part))
                else:
                    raise Exception(f'Several type modules are passed {type(part)}')
            else:
                raise Exception(f'{type(part)} is not BasePart')
        self._parts = tuple(parts_ok)

    def get_part(self, type_part):
        for part in self._parts:
            if type(part) == type_part:
                return part
        raise None

    def start(self):
        if self._is_update:
            raise Exception('Controller is ready')
        self._is_update = True

        _thread.start_new_thread(self._start_loop, (_startups_thread, _updates_thread, _shutdowns_thread, True))
        self._start_loop(_startups, _updates, _shutdowns)

    def _start_loop(self, startups, updates, shutdowns, thread=False):
        logger = getLogger('thread1' if thread else 'thread0')

        def run(c):
            try:
                c(self)
                return True
            except Exception as e:
                logger.error(f'Error loop callback: {str(e)}')
                return False
        if thread:
            while not self._started_thread0:
                utime.sleep(0.01)
        if not self._is_update:
            return
        logger.info(f"Start loop...")
        logger.info(f"Run startups...")
        for startup in startups:
            if not run(startup.function):
                self._is_update = False
                logger.error(f"Loop closed")
                return

        intervals_call = tuple(set(i.freq for i in updates))
        functions_call = {i.freq: tuple(j.callback for j in updates if j.freq == i.freq) for i in updates}
        last_call = {i: utime.ticks_cpu() for i in intervals_call}

        logger.info(f"Loop started")
        if not thread:
            self._started_thread0 = True
        while self._is_update:
            try:
                t = utime.ticks_cpu()
                for interval in intervals_call:
                    if utime.ticks_diff(t, last_call[interval]) >= interval:
                        for c in functions_call[interval]:
                            run(c)
                        last_call[interval] = t
            except (KeyboardInterrupt, SystemExit):
                break
        logger.info(f"Close Loop...")

        self._is_update = False
        logger.info(f"Run shutdowns...")
        for shutdown in shutdowns:
            run(shutdown.function)
        logger.info(f"Loop closed")
