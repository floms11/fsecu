import sys

DEBUG = 0
INFO = 1
WARNING = 2
ERROR = 3
CRITICAL = 4

LEVELS_TEXT = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

DEFAULT_LEVEL = DEBUG


class Logger:
    __name: str
    __level: int = DEFAULT_LEVEL

    def __init__(self, name: str):
        self.__name = name

    def debug(self, message):
        return self.log(DEBUG, message)

    def info(self, message):
        return self.log(INFO, message)

    def warning(self, message):
        return self.log(WARNING, message)

    def error(self, message):
        return self.log(ERROR, message)

    def critical(self, message):
        return self.log(CRITICAL, message)

    def setLevel(self, level):
        self.__level = level

    def log(self, level, message):
        if level >= self.__level:
            self.write_log(level, f"{LEVELS_TEXT[level]:<8} | {self.__name:<30} {message}\n")

    def write_log(self, level, text):
        sys.stderr.write(text)


def getLogger(name=None):
    if name is None:
        name = ''
    return Logger(name)

