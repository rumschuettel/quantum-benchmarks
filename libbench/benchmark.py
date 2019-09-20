from abc import ABC, abstractmethod
from typing import List, Dict

from .link import VendorJob


class VendorBenchmark(ABC):
    """
    Vendor benchmark interface.
    """
    @abstractmethod
    def get_jobs(self) -> List[VendorJob]:
        raise NotImplementedError()

    @abstractmethod
    def parse_result(self, job, result):
        raise NotImplementedError()

    @abstractmethod
    def collate_results(self, results: List[Dict[VendorJob, object]]):
        raise NotImplementedError()