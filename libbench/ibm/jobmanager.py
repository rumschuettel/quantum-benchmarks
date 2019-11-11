from libbench import VendorJobManager, print_stderr
from .benchmark import IBMBenchmark

from .link import IBMDevice

from qiskit.providers import JobStatus
from qiskit.providers.ibmq.api_v2.exceptions import ApiError

import datetime, dateutil


def utc_timestamp():
    return datetime.datetime.utcnow().isoformat()


def time_elapsed(then: str):
    # current time in UTC format
    now = utc_timestamp()
    now = dateutil.parser.parse(now)
    then = dateutil.parser.parse(then)
    return now - then


class IBMJobManager(VendorJobManager):
    # maximum time for a job to be considered a failure
    MAX_JOB_AGE = datetime.timedelta(minutes=10)

    def job_alive(self, promise, meta: dict):
        """
            check whether we consider the job behind the promise alive on an IBM backend
        """
        # note that if this fails due to e.g. a TimeoutError
        # this does not mean that the job is broken;
        # it could e.g. be a network issue. We let that error propagate
        status = promise.status()
        print("The job is reported to be in status: \""+ str(status)+"\"")
        
        if status in [JobStatus.QUEUED, JobStatus.RUNNING, JobStatus.DONE]:
            return True

        elif status in [JobStatus.ERROR, JobStatus.CANCELLED]:
            return False

        # check whether status has been like this before
        if "first_running_status_time_of_"+str(status) in meta:
            then = meta["first_running_status_time_of_"+str(status)]
        # otherwise mark status to be in this state for the first time
        else:
            then = meta["first_running_status_time_of_"+str(status)] = utc_timestamp()

        # calculate time difference; if below threshold all is ok
        age = time_elapsed(then)

        if age <= self.MAX_JOB_AGE:
            return True
        
        # otherwise try to cancel old job
        print("The job seems stuck is status: \""+ str(status) +"\" for more than "+ str(age.seconds) +" seconds, trying to cancel it.")
        try:
            promise.cancel()
            del meta["first_running_status_time_of_"+str(status)]
        except ApiError as e:
            print_stderr(e)
        finally:
            return False

    def queued_successfully(self, promise, meta: dict):
        """
            check whether we consider the job behind the promise queued, or more than queued, on an IBM backend;
            this happens to coincide with self.job_alive; however we should also check whether job_id is successful
            since only that makes a call to the cloud backend
        """
        if not self.job_alive(promise, meta):
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

    def try_get_results(self, promise, device: IBMDevice):
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

    def thaw_promise(self, job_id, device: IBMDevice):
        """
            load job by job_id
        """
        return device.device.retrieve_job(job_id)
