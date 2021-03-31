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

    def gate_statistics(self):
        """
            TODO: do something with jobs[i].device_info
        """
        from collections import defaultdict
        import numpy as np

        jobs = self.results.keys()
        gatestats = defaultdict(list)

        for job in jobs:
            for slug in job.device_info.values():
                for sslug in slug.values():
                    for param, value in sslug.items():
                        if value is not None:
                            gatestats[param].append(value)

        for key, value in gatestats.items():
            gatestats[key] = (np.mean(value), np.std(value))
        
        return {
            "gates": dict(gatestats),
            "date": None
        }