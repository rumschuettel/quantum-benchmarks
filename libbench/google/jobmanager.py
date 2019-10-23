from libbench import VendorJobManager
from .benchmark import GoogleBenchmark

import cirq


class GoogleJobManager(VendorJobManager):
    def job_alive(self, promise):
        """
            Check whether the job is alive.
        """
        return promise.status() in ["PENDING", "DONE"]

    def queued_successfully(self, promise):
        """
            Check whether the job is successfully queued.
        """
        return promise.status() in ["PENDING", "DONE"]

    def try_get_results(self, promise, device):
        """
            Obtain job results when done.
            For now we only have simulators that finish immediately.
        """
        return promise.result()

    def freeze_promise(self, promise):
        """
            Freeze a promise.
        """
        return promise.freeze()

    def thaw_promise(self, promise):
        """
            Thaw a promise.
        """
        return promise.thaw()
