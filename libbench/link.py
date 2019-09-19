from abc import ABC, abstractmethod

class VendorLink(ABC):
    """
    Vendor link interface
    all methods in here have to be implemented for a valid link
    """
    @abstractmethod
    def list_devices(self):
        """return an array of devices"""
        pass



class Job(ABC):
    """
    Job interface.
    This
    """