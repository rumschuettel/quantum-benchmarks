from abc import ABC, abstractmethod


class VendorJob(ABC):
    """
    Vendor job interface.
    """
    @abstractmethod
    def run(self, *args):
        raise NotImplementedError()


class VendorLink(ABC):
    """
    Vendor link interface
    all methods in here have to be implemented for a valid link
    """
    @abstractmethod
    def get_devices(self):
        raise NotImplementedError()


    @abstractmethod
    def run(self, job: VendorJob):
        raise NotImplementedError()


