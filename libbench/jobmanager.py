import pickle, os
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Optional, Callable

from .benchmark import VendorBenchmark
from .lib import benchmark_id, print_hl, print_stderr


class VendorJobManager(ABC):
    RUN_FOLDER = "./runs"
    JOBMANAGER_FILENAME = "jobmanager.pickle"
    COLLATED_FILENAME = "collated.pickle"
    VISUALIZED_FILENAME = "visualized.pickle"
    JOBS_FOLDER = "jobs"
    MAX_FAILURE_COUNT = 1
    MAX_QUEUE_COUNT = 10 ** 6

    def __init__(self, benchmark: VendorBenchmark):
        self.benchmark = benchmark
        self.scheduled = benchmark.get_jobs()
        self.ID = self.VENDOR + "-" + str(benchmark) + "--" + benchmark_id()

        self.queued = {}  # job: promise
        self.results = {}  # job: result

    def update(
        self,
        device,
        additional_stored_info: Optional[dict] = None,
        figure_callback: Callable[[Path], None] = lambda *_: None,
        store_job_and_results=True,
        store_jobmanager=True,
        store_additional_info=True,
        display_status=True,
    ) -> Optional[object]:
        # try to queue more jobs
        new_scheduled = []
        failure_counter = 0

        for job in self.scheduled:
            if failure_counter >= self.MAX_FAILURE_COUNT or len(self.queued) > self.MAX_QUEUE_COUNT:
                new_scheduled.append(job)
                continue

            # try to obtain result
            response = job.run(device)
            promise = response["result"]
            job.transpiled_circuit = response["transpiled_circuit"]

            if self.queued_successfully(promise, job.meta):
                print(f"{str(job)} successfully queued.")
                self.queued[job] = promise
                failure_counter = 0
            else:
                print(f"Could not queue {str(job)}.")
                new_scheduled.append(job)
                failure_counter += 1

        self.scheduled = new_scheduled

        # try to obtain more results
        new_queued = {}
        for job in self.queued:
            promise = self.queued[job]

            # 1. we try to get the result
            result = self.try_get_results(promise, device)
            if result is not None:
                print(f"{job} completed.")
                self.results[job] = self.benchmark.parse_result(job, result)

                # store job results separately in addition
                if store_job_and_results:
                    self._save_in_run_folder(f"jobs/{str(job)}.raw-result.pickle", result)
                    self._save_in_run_folder(f"jobs/{str(job)}.pickle", self.results[job])
                    self._save_in_run_folder(f"jobs/{str(job)}.circuit.pickle", job.serialize())
                    self._save_in_run_folder(f"jobs/{str(job)}.circuit.qasm", job.qasm(), pickle_dump = False)

            # 2. if that failed, check whether job is alive and if not reschedule
            elif not self.job_alive(promise, job.meta):
                self.scheduled = [job] + self.scheduled
                print(f"The job {job} has been rescheduled")

            # 3. otherwise the job simply wasn't done, put back to queue
            else:
                new_queued[job] = promise

        self.queued = new_queued

        # store jobmanager for reuse
        if store_jobmanager:
            self.save(additional_stored_info)

        if store_additional_info:
            self.save_additional_info_files(additional_stored_info)

        # if all are done, we can finalize the result
        if len(self.scheduled) == 0 and len(self.queued) == 0:
            print_hl(f"benchmark {self.ID} completed.")
            self.finalize(figure_callback)
            return True

        # otherwise print status
        self.print_legend()
        self.print_status()
        return False

    def collate_results(self):
        return self.benchmark.collate_results(self.results)

    def visualize_results(self, collated_result):
        path = Path(self.RUN_FOLDER) / self.ID
        return self.benchmark.visualize(collated_result, path)

    def score(self, collated_result, reference_collated_result):
        return self.benchmark.score(collated_result, reference_collated_result)

    def finalize(
        self,
        figure_callback=lambda *_: None,
        backup_collated_result=True,
        backup_visualized_result=False,
    ):
        """
        collate results, visualize, and call visualization callback
        """

        collated_result = self.collate_results()
        print("Collated.")

        if backup_collated_result:
            self._save_in_run_folder(self.COLLATED_FILENAME, collated_result)
            print(f"Backup written to {self.RUN_FOLDER}/{self.ID}/{self.COLLATED_FILENAME}.")

        visualized_result = self.visualize_results(collated_result)
        figure_callback(visualized_result)
        print("Visualized.")

        if backup_visualized_result:
            self._save_in_run_folder(self.VISUALIZED_FILENAME, visualized_result)
            print(f"Backup  written to {self.RUN_FOLDER}/{self.ID}/{self.VISUALIZED_FILENAME}.")

        return True

    @staticmethod
    def print_legend():
        print("Job status: ", end="")
        print_hl("scheduled", color="red", end=" ")
        print_hl("queued", color="yellow", end=" ")
        print_hl("completed", color="green", end="")
        print(".")

    def print_status(self, tail: str = ""):
        status = self.status()

        print(self.ID, end=": ")
        print_hl(str(status["scheduled"]), color="red", end=" ")
        print_hl(str(status["queued"]), color="yellow", end=" ")
        print_hl(str(status["completed"]), color="green")
        if tail:
            print("  ", tail)
            print("  ", str(repr(self.benchmark)))

    def status(self):
        return {
            "scheduled": len(self.scheduled),
            "queued": len(self.queued),
            "completed": len(self.results),
        }

    @property
    def done(self):
        status = self.status()
        return status["scheduled"] == 0 and status["queued"] == 0

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

    def save_additional_info_files(self, additional_stored_info):
        for key, what in additional_stored_info.items():
            self._save_in_run_folder(f"{what}.{key}")

    def _save_in_run_folder(self, filename: str, obj: object = None, pickle_dump: bool = True):
        full_filename = f"{self.RUN_FOLDER}/{self.ID}/{filename}"
        full_folder = os.path.dirname(full_filename)
        if not os.path.exists(full_folder):
            os.makedirs(full_folder)

        if pickle_dump:
            with open(full_filename, 'wb') as f:
                pickle.dump(obj, f)
        else:
            with open(full_filename, 'w') as f:
                f.write(obj)

    @classmethod
    def load(clx, ID):
        with open(f"{clx.RUN_FOLDER}/{ID}/{clx.JOBMANAGER_FILENAME}", "rb") as f:
            slug = pickle.load(f)
            assert slug["jobmanager"].ID == ID, "instance ID does not match passed ID"
            return slug

    def print_gate_statistics(self):
        assert self.done, "benchmark not done yet"
        stats = self.gate_statistics()
        print(f"date: {stats['date']}, gates: ", end="")
        for g, (v, e) in stats["gates"].items():
            print(f"{g} {v:.02e} ± {e:.02e}  ", end="")
        print("")

    @abstractmethod
    def gate_statistics(self):
        pass

    def thaw(self, device):
        # thaw queued promises
        for job in list(self.queued):
            thawed_promise = self.thaw_promise(self.queued[job], device)
            if thawed_promise is None:
                print_stderr(f"could not thaw job {job}; rescheduling")
                self.scheduled.append(job)
                del self.queued[job]

            else:
                self.queued[job] = self.thaw_promise(self.queued[job], device)

    @abstractmethod
    def queued_successfully(self, promise, meta: dict) -> bool:
        pass

    @abstractmethod
    def freeze_promise(self, promise):
        """
        transform promise into something we can pickle
        """
        pass

    @abstractmethod
    def thaw_promise(self, promise_id, device):
        """
        restore promise from pickled object
        """
        pass

    @abstractmethod
    def job_alive(self, promise, meta: dict) -> bool:
        pass

    @abstractmethod
    def try_get_results(self, promise, device) -> Optional[object]:
        pass
