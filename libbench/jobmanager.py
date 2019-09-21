import pickle, os
from abc import ABC, abstractmethod
from typing import Optional

from .benchmark import VendorBenchmark
from .lib import benchmark_id


class VendorJobManager(ABC):
    scheduled = []  # list of jobs
    queued = {}  # job: promise
    results = {}  # job: result

    RUN_FOLDER = "./runs"
    JOBMANAGER_FILENAME = "jobmanager.pickle"
    COLLATED_FILENAME = "collated.pickle"
    JOBS_FOLDER = "jobs"

    def __init__(self, benchmark: VendorBenchmark, ID: Optional[str] = None):
        self.benchmark = benchmark
        self.scheduled = benchmark.get_jobs()
        self.ID = ID if ID is not None else benchmark_id()

    def update(
        self, device, store_completed_job_results=True, store_collated_result=True, store_jobmanager=True
    ) -> Optional[object]:
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
                print(f"{str(job)} completed.")
                self.results[job] = self.benchmark.parse_result(job, result)

                # store job results separately in addition
                if store_completed_job_results:
                    self._save_in_run_folder(f"jobs/{str(job)}.pickle", self.results[job])
            else:
                new_queued[job] = promise
        self.queued = new_queued

        # store jobmanager for reuse
        if store_jobmanager:
            self.save()

        # if all are done, we can collate the results and potentially store it
        if len(self.scheduled) == 0 and len(self.queued) == 0:
            print_hl(f"benchmark {self.ID} completed.")
            collated_result = self.benchmark.collate_results(self.results)
            if store_collated_result:
                self._save_in_run_folder(self.COLLATED_FILENAME, collated_result)
            return collated_result


    def save(self):
        self._save_in_run_folder(self.JOBMANAGER_FILENAME, self)

    def _save_in_run_folder(self, filename: str, obj: object):
        full_filename = f"{self.RUN_FOLDER}/{self.ID}/{filename}"
        full_folder = os.path.dirname(full_filename)
        if not os.path.exists(full_folder):
            os.makedirs(full_folder)

        with open(full_filename, "wb") as f:
            pickle.dump(obj, f)

    @classmethod
    def load(clx, ID):
        with open(f"{clx.RUN_FOLDER}/{ID}/", "rb") as f:
            instance = pickle.load(f)
            assert instance.ID == ID, "instance ID does not match passed ID"
            return instance

    @abstractmethod
    def queued_successfully(self, promise) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def try_get_results(self, promise) -> Optional[object]:
        raise NotImplementedError()
