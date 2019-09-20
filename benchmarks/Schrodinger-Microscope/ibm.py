from libbench import VendorBenchmark, VendorJob


class IBMBenchmark(VendorBenchmark):
    def __init__(self):
        super().__init__()

    
    def get_jobs(self):
        return 0