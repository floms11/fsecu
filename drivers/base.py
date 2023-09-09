class BaseDriver:
    freq_update: int = 0

    def __init__(self):
        from controller import Startup, Shutdown, Update
        Startup(self._startup)
        Shutdown(self._shutdown)
        if self.freq_update > 0:
            Update(self._update, self.freq_update)

    def _startup(self, controller):
        pass

    def _shutdown(self, controller):
        pass

    def _update(self, controller):
        pass
