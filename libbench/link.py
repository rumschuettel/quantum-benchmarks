from abc import ABC, abstractmethod
from typing import Dict, Callable


class ThinPromise(ABC):
    """
        This is a thin promise that simply executes the given callback,
        and otherwise mimics the IBM interface.

        This can be used as a promise whenever the execution is immediate.
    """

    def __init__(self, result_callback: Callable, *args, **kwargs):
        self._result = None
        self.result_callback = result_callback
        self.args = args
        self.kwargs = kwargs

    def job_id(self):
        return id(self)

    def status(self):
        return "PENDING" if self._result is None else "DONE"

    def result(self):
        if self._result is None:
            self._result = self.result_callback(*self.args, **self.kwargs)
        return self._result


class VendorJob(ABC):
    """
    Vendor job interface.
    """

    @abstractmethod
    def run(self, *args, id):
        pass

    @abstractmethod
    def __str__(self):
        pass

    @abstractmethod
    def serialize(self):
        pass


class VendorLink(ABC):
    """
    Vendor link interface
    all methods in here have to be implemented for a valid link
    """

    @abstractmethod
    def get_devices(self) -> Dict[str, object]:
        pass

    def get_device(self, name):
        return self.get_devices()[name]
