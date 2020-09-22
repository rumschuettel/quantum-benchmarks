from abc import ABC, abstractmethod
from typing import Dict, Callable, Tuple, List, Union


class ThinPromise(ABC):
    """
    This is a thin promise that simply executes the given callback,
    and otherwise mimics the IBM interface.

    This can be used as a promise whenever the execution is immediate.
    """

    def __init__(self, result_callback: Callable, *args, **kwargs):
        self._result = result_callback(*args, **kwargs)

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

    def __init__(self):
        self.device_info = None
        self.transpiled_circuit = None
        self.meta = {}  # additional information that can be stored alongside job

    @abstractmethod
    def run(self, device):
        pass

    @abstractmethod
    def __str__(self):
        pass

    @abstractmethod
    def serialize(self):
        return {"device_info": None, "transpiled_circuit": self.transpiled_circuit}


class VendorLink(ABC):
    """
    Vendor link interface
    all methods in here have to be implemented for a valid link
    """

    @abstractmethod
    def get_devices(self) -> Dict[str, object]:
        pass

    @abstractmethod
    def get_device_topology(self, name) -> Union[Dict[Tuple[int, int], float], None]:
        pass

    def get_device(self, name):
        return self.get_devices()[name]
