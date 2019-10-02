import pickle, os
from abc import ABC, abstractmethod
from typing import Optional

from .benchmark import VendorBenchmark
from .lib import benchmark_id, print_hl


MAX_FAILURE_COUNT = 10

class VendorJobManager(ABC):
    RUN_FOLDER = "./runs"
    JOBMANAGER_FILENAME = "jobmanager.pickle"
    COLLATED_FILENAME = "collated.pickle"
    JOBS_FOLDER = "jobs"

    def __init__(self, benchmark: VendorBenchmark):
        self.benchmark = benchmark
        self.scheduled = benchmark.get_jobs()
        self.ID = benchmark_id()

        self.queued = {}  # job: promise
        self.results = {}  # job: result

    def update(
        self,
        device,
        additional_stored_info: Optional[dict] = None,
        store_completed_job_results=True,
        store_collated_result=True,
        store_jobmanager=True,
    ) -> Optional[object]:
        # try to queue more jobs
        new_scheduled = []
        failure_counter = 0
        for job in self.scheduled:
            promise = job.run(device)
            if self.queued_successfully(promise):
                print(f"{str(job)} successfully queued.")
                self.queued[job] = promise
                failure_counter = 0
            else:
                print(f"Could not queue {str(job)}.")
                new_scheduled.append(job)
                failure_counter += 1
            if failure_counter >= MAX_FAILURE_COUNT:
                print(f"{MAX_FAILURE_COUNT} consecutive failures to queue, so refraining from trying again.")
                break
        self.scheduled = new_scheduled

        # try to obtain more results
        new_queued = {}
        for job in self.queued:
            promise = self.queued[job]

            # 1. we try to get the result
            result = self.try_get_results(promise, device)
            if result is not None:
                print(f"{str(job)} completed.")
                self.results[job] = self.benchmark.parse_result(job, result)

                # store job results separately in addition
                if store_completed_job_results:
                    self._save_in_run_folder(f"jobs/{str(job)}.pickle", self.results[job])

            # 2. if that failed, check whether job is alive and if not reschedule
            elif not self.job_alive(promise):
                self.scheduled.append(job)

            # 3. otherwise the job simply wasn't done, put back to queue
            else:
                new_queued[job] = promise
        self.queued = new_queued

        # store jobmanager for reuse
        if store_jobmanager:
            self.save(additional_stored_info)

        # if all are done, we can collate the results and potentially store it
        if len(self.scheduled) == 0 and len(self.queued) == 0:
            print_hl(f"benchmark {self.ID} completed.")
            collated_result = self.benchmark.collate_results(self.results)
            if store_collated_result:
                self._save_in_run_folder(self.COLLATED_FILENAME, collated_result)
            return collated_result

    def save(self, additional_stored_info):
        # freeze promise queue into something pickleable
        old_queued = self.queued.copy()

        for job in self.queued:
            self.queued[job] = self.freeze_promise(self.queued[job])

        self._save_in_run_folder(
            self.JOBMANAGER_FILENAME,
            {"jobmanager": self, "additional_stored_info": additional_stored_info},
        )

        # restore queue
        self.queued = old_queued

    def _save_in_run_folder(self, filename: str, obj: object):
        full_filename = f"{self.RUN_FOLDER}/{self.ID}/{filename}"
        full_folder = os.path.dirname(full_filename)
        if not os.path.exists(full_folder):
            os.makedirs(full_folder)

        with open(full_filename, "wb") as f:
            pickle.dump(obj, f)

    @classmethod
    def load(clx, ID):
        with open(f"{clx.RUN_FOLDER}/{ID}/{clx.JOBMANAGER_FILENAME}", "rb") as f:
            slug = pickle.load(f)
            assert slug["jobmanager"].ID == ID, "instance ID does not match passed ID"
            return slug

    def thaw(self, device):
        # thaw queued promises
        for job in self.queued:
            self.queued[job] = self.thaw_promise(self.queued[job], device)

    @abstractmethod
    def queued_successfully(self, promise) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def freeze_promise(self, promise):
        """
            transform promise into something we can pickle
        """
        raise NotImplementedError()

    @abstractmethod
    def thaw_promise(self, promise_id, device):
        """
            restore promise from pickled object
        """
        raise NotImplementedError()

    @abstractmethod
    def job_alive(self, promise) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def try_get_results(self, promise, device) -> Optional[object]:
        raise NotImplementedError()
