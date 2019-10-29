from abc import ABC, abstractmethod
from pathlib import Path
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
    def collate_results(self, results: Dict[VendorJob, object], path: Path):
        pass

    @abstractmethod
    def visualize(self, results: object, path: Path):
        pass

    @abstractmethod
    def __str__(self):
        pass

    @abstractmethod
    def __repr__(self):
        pass
