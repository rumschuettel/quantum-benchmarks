from abc import ABC, abstractmethod
from typing import Optional

from .benchmark import VendorBenchmark

class VendorJobManager(ABC):
    scheduled = [] # list of jobs
    queued = {} # job: promise
    results = {} # job: result

    def __init__(self, benchmark: VendorBenchmark):
        self.benchmark = benchmark
        self.scheduled = benchmark.get_jobs()

    def update(self, device) -> Optional[object]:
        # try to queue more jobs
        new_scheduled = []
        for job in self.scheduled:
            promise = job.run(device)
            if self.queued_successfully(promise):
                self.queued[job] = promise
            else:
                new_scheduled.append(job)
        self.scheduled = new_scheduled

        # try to obtain more results
        new_queued = {}
        for job in self.queued:
            promise = self.queued[job]
            result = self.try_get_results(promise)
            if result is not None:
                self.results[job] = self.benchmark.parse_result(job, result)
            else:
                new_queued[job] = promise
        self.queued = new_queued

        # if all are done, we can collate the results
        if len(self.scheduled) == 0 and len(self.queued) == 0:
            return self.benchmark.collate_results(self.results)


    @abstractmethod
    def queued_successfully(self, promise) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def try_get_results(self, promise) -> Optional[object]:
        raise NotImplementedError()
