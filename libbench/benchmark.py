from abc import ABC, abstractmethod
from typing import List

from .link import VendorJob


class VendorBenchmark(ABC):
    """
    Vendor benchmark interface.
    """

    @abstractmethod
    def get_jobs(self) -> List[VendorJob]:
        raise NotImplementedError()

