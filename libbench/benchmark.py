from abc import ABC, abstractmethod
from typing import List, Dict

from .link import VendorJob


class VendorBenchmark(ABC):
    """
    Vendor benchmark interface.
    """

    @abstractmethod
    def get_jobs(self) -> List[VendorJob]:
        pass

    @abstractmethod
    def parse_result(self, job, result):
        pass

    @abstractmethod
    def collate_results(self, results: Dict[VendorJob, object]):
        pass

    @abstractmethod
    def __str__(self):
        pass
