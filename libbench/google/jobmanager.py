from libbench import VendorJobManager


class GoogleJobManager(VendorJobManager):
    VENDOR = 'Google'
    
    def job_alive(self, promise, meta: dict):
        """
        Check whether the job is alive.
        """
        return promise.status() in ["PENDING", "DONE"]

    def queued_successfully(self, promise, meta: dict):
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

    def thaw_promise(self, promise, _):
        """
        Thaw a promise.
        """
        return promise.thaw()

    def gate_statistics(self):
        """
        Get statistics of gate fidelities
        """
        return {}
