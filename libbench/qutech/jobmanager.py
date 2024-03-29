from libbench import VendorJobManager, print_stderr
from .benchmark import QuTechBenchmark

from .link import QuTechDevice

from qiskit.providers import JobStatus
from quantuminspire.exceptions import ApiError

import datetime, dateutil


def utc_timestamp():
    return datetime.datetime.utcnow().isoformat()


def time_elapsed(then: str):
    # current time in UTC format
    now = utc_timestamp()
    now = dateutil.parser.isoparse(now)
    then = dateutil.parser.isoparse(then)
    return now - then


class QuTechJobManager(VendorJobManager):
    VENDOR = 'QuTech'

    # maximum time for a job to be considered a failure
    MAX_JOB_AGE = datetime.timedelta(minutes=60*24*2)

    def job_alive(self, promise, meta: dict):
        """
        check whether we consider the job behind the promise alive on an QuTech backend; however we should also check whether job_id is successful
        since only that makes a call to the cloud backend
        """
        try:
            id = promise.job_id()

        except ApiError as e:
            message = str(e)
            if "Please wait for those jobs to finish or cancel a job." in str(e):
                print_stderr(str(e))
                return False

            raise

        # note that if this fails due to e.g. a TimeoutError
        # this does not mean that the job is broken;
        # it could e.g. be a network issue. We let that error propagate
        status = promise.status()
        print(f"The job with QuTech ID {id} is reported to be in status: {status}")

        if status in [JobStatus.QUEUED, JobStatus.RUNNING, JobStatus.DONE]:
            return True

        elif status in [JobStatus.ERROR, JobStatus.CANCELLED, "FAILURE"]:
            return False

        # check whether status has been like this before
        if not "last-status" in meta or meta["last-status"]["status"] != status:
            meta["last-status"] = {"status": status, "time": utc_timestamp()}
            return True

        # calculate time difference; if below threshold all is ok
        age = time_elapsed(meta["last-status"]["time"])
        if age <= self.MAX_JOB_AGE:
            return True

        # otherwise try to cancel old job
        print(
            f"The job with QuTech ID {id} seems stuck in status: {status} for more than {age}, trying to cancel it."
        )
        try:
            promise.cancel()
            del meta["last-status"]
        except ApiError as e:
            print_stderr(str(e))
        finally:
            return False

    def queued_successfully(self, promise, meta: dict):
        """
        check whether we consider the job behind the promise queued, or more than queued, on an QuTech backend;
        this happens to coincide with self.job_alive
        """
        if not self.job_alive(promise, meta):
            return False

        return True

    def try_get_results(self, promise, device: QuTechDevice):
        """
        obtain job results when done
        """
        if device.device.name() in ["statevector_simulator", "qasm_simulator"]:
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

    def thaw_promise(self, job_id, device: QuTechDevice):
        """
        load job by job_id
        """
        try:
            return device.device.retrieve_job(job_id)
        except ApiError as e:
            print_stderr(str(e))
            return None

    def gate_statistics(self):
        """
        Get statistics of gate fidelities
        """
        return {"date": None, "gates": {}}
