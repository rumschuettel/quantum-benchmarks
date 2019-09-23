from libbench import VendorJobManager
from .benchmark import GoogleBenchmark

import cirq


class GoogleJobManager(VendorJobManager):
    def __init__(self, benchmark: GoogleBenchmark):
        super().__init__(benchmark)

    def job_alive(self, promise):
        """
            Check whether the job is alive.
        """
        return True

    def queued_successfully(self, promise):
        """
            Check whether the job is successfully queued.
        """
        return True

    def try_get_results(self, promise, device):
        """
            Obtain job results when done.
        """
        return promise.result()

    def freeze_promise(self, promise):
        """
            Freeze a promise.
        """
        return promise.freeze()

    def thaw_promise(self, obj):
        """
            Thaw a promise.
        """
        return promise.thaw()
