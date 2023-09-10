class BaseDriver:
    delay_update: int = 0
    thread: bool = False

    def __init__(self):
        from controller import Startup, Shutdown, Update
        Startup(self._startup, thread=self.thread)
        Shutdown(self._shutdown, thread=self.thread)
        if self.delay_update > 0:
            Update(self._update, self.delay_update, thread=self.thread)

    def _startup(self, controller):
        pass

    def _shutdown(self, controller):
        pass

    def _update(self, controller):
        pass
