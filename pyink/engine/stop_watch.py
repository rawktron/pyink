import time


class Stopwatch:
    def __init__(self):
        self._start_time = None

    @property
    def ElapsedMilliseconds(self) -> int:
        if self._start_time is None:
            return 0
        return int((time.time() - self._start_time) * 1000)

    def Start(self):
        self._start_time = time.time()

    def Stop(self):
        self._start_time = None
