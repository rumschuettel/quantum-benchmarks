from libbench import VendorJobManager
from .benchmark import IBMBenchmark


class IBMJobManager(VendorJobManager):
    def __init__(self, benchmark: IBMBenchmark):
        super().__init__(benchmark)

    def queued_successfully(self, promise):
        return True

    def try_get_results(self, promise):
        return promise.result()
