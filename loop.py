import utime

FREQ_VERY_FAST = 100
FREQ_FAST = 1000
FREQ_NORMAL = 10000
FREQ_MEDIUM = 50000
FREQ_SLOW = 100000
FREQ_VERY_SLOW = 1000000


callbacks = {
    FREQ_VERY_FAST: [],
    FREQ_FAST: [],
    FREQ_NORMAL: [],
    FREQ_MEDIUM: [],
    FREQ_SLOW: [],
    FREQ_VERY_SLOW: [],
}


class Loop:
    def __init__(self, callback, freq=FREQ_NORMAL):
        global callbacks
        callbacks[freq].append(callback)


def startup(vf: tuple, f: tuple, n: tuple, m: tuple, s: tuple, vs: tuple):
    tovf: int = 0
    tof: int = 0
    ton: int = 0
    tom: int = 0
    tos: int = 0
    tovs: int = 0
    t: int = 0

    def run(c):
        try:
            c()
        except Exception as e:
            print(f'Помилка зворотнього виклику: {str(e)}')

    while True:
        utime.sleep_us(1)
        t = utime.ticks_cpu()
        if utime.ticks_diff(t, tovf) >= FREQ_VERY_FAST:
            for c in vf:
                run(c)
            tovf = t
            if utime.ticks_diff(t, tof) >= FREQ_FAST:
                for c in f:
                    run(c)
                tof = t
                if utime.ticks_diff(t, ton) >= FREQ_NORMAL:
                    for c in n:
                        run(c)
                    ton = t
                    if utime.ticks_diff(t, tom) >= FREQ_MEDIUM:
                        for c in m:
                            run(c)
                        tom = t
                        if utime.ticks_diff(t, tos) >= FREQ_SLOW:
                            for c in s:
                                run(c)
                            tos = t
                            if utime.ticks_diff(t, tovs) >= FREQ_VERY_SLOW:
                                for c in vs:
                                    run(c)
                                tovs = t


def start():
    startup(
        tuple(callbacks[FREQ_VERY_FAST]),
        tuple(callbacks[FREQ_FAST]),
        tuple(callbacks[FREQ_NORMAL]),
        tuple(callbacks[FREQ_MEDIUM]),
        tuple(callbacks[FREQ_SLOW]),
        tuple(callbacks[FREQ_VERY_SLOW]),
    )
