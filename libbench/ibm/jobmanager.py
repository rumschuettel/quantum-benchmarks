from libbench import VendorJobManager
from .benchmark import IBMBenchmark

from qiskit.providers import JobStatus
from qiskit.providers.ibmq.api_v2.exceptions import ApiError


class IBMJobManager(VendorJobManager):
    def __init__(self, benchmark: IBMBenchmark):
        super().__init__(benchmark)

    def job_alive(self, promise):
        """
            check whether we consider the job behind the promise alive on an IBM backend
        """
        return promise.status() in [
            JobStatus.DONE,
            JobStatus.INITIALIZING,
            JobStatus.QUEUED,
            JobStatus.RUNNING,
            JobStatus.VALIDATING,
        ]

    def queued_successfully(self, promise):
        """
            check whether we consider the job behind the promise queued, or more than queued, on an IBM backend;
            this happens to coincide with self.job_alive; however we should also check whether job_id is successful
            since only that makes a call to the cloud backend
        """
        if not self.job_alive(promise):
            return False

        try:
            promise.job_id()

        except ApiError as e:
            message = e.message.rstrip("\n .")
            if message.endswith("QUEUE_DISABLED"):
                print("The queue for this device is disabled.")
                return False
            elif message.endswith("NOT_CREDITS_AVALIABLES"):
                print("You don't have enough credits to run this job.")
                return False

            raise

        return True

    def try_get_results(self, promise, device):
        """
            obtain job results when done
        """
        if device.name() in ["statevector_simulator", "qasm_simulator"]:
            return promise.result()

        if not promise.status() == JobStatus.DONE:
            return None

        return promise.result()

    def freeze_promise(self, promise):
        """
            transform promise into something pickleable.
            we know this is called after queued_success was True, so job_id exists
        """
        return promise.job_id()

    def thaw_promise(self, job_id, device):
        """
            load job by job_id
        """
        return device.retrieve_job(job_id)
