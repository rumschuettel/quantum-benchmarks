from abc import ABC, abstractmethod
from typing import Dict, Callable


class ThinPromise(ABC):
    """
        This is a thin promise that simply executes the given callback,
        and otherwise mimics the IBM interface.

        This can be used as a promise whenever the execution is immediate.
    """

    def __init__(self, result_callback: Callable, *args, **kwargs):
        try:
            self._result = result_callback(*args, **kwargs)
        except:
            pass

    def job_id(self):
        return id(self)

    def status(self):
        return "FAILURE" if self._result is None else "DONE"

    def result(self):
        return self._result

    def freeze(self):
        return self
    
    def thaw(self):
        return self


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
