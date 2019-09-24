from abc import ABC, abstractmethod
from typing import Dict


class VendorJob(ABC):
    """
    Vendor job interface.
    """

    @abstractmethod
    def run(self, *args, id):
        raise NotImplementedError()

    @abstractmethod
    def __str__(self):
        raise NotImplementedError()


class VendorLink(ABC):
    """
    Vendor link interface
    all methods in here have to be implemented for a valid link
    """

    @abstractmethod
    def get_devices(self) -> Dict[str, object]:
        raise NotImplementedError()

    def get_device(self, name):
        return self.get_devices()[name]

