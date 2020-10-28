from libbench import VendorJobManager
from .benchmark import RigettiBenchmark

import pyquil as pq


class RigettiJobManager(VendorJobManager):
    def job_alive(self, promise, meta: dict):
        """
        Check whether the job is alive.
        """
        return promise.status() == "DONE"

    def queued_successfully(self, promise, meta: dict):
        """
        Check whether the job is successfully queued.
        """
        return promise.status() == "DONE"

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

    def thaw_promise(self, promise):
        """
        Thaw a promise.
        """
        return promise.thaw()
