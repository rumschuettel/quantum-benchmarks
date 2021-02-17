import numpy as np

from libbench.amazon import Benchmark as AmazonBenchmark

from .job import HHLJob
from .. import HHLBenchmarkMixin


class HHLBenchmarkBase(HHLBenchmarkMixin, AmazonBenchmark):
    def __init__(self, add_measurements, **kwargs):
        super().__init__(**kwargs)

        self.add_measurements = add_measurements

    def get_jobs(self):
        yield from HHLJob.job_factory(
            self.matrix,
            self.num_shots,
            self.shots_multiplier,
            self.add_measurements,
        )

    def __str__(self):
        return "Amazon-HHL"


class HHLBenchmark(HHLBenchmarkBase):
    """
    Full Benchmark

    Either a cloud device, or a local simulator
    """

    def __init__(self, *args, **kwargs):
        kwargs.update({"add_measurements": True})
        super().__init__(*args, **kwargs)

    def parse_result(self, job, result):
        counts = result.measurement_counts

        total = 0
        histogram = [0] * 2 ** (job.num_qubits-job.num_ancillas)
        for result in counts.keys():
            total += counts.get(result)
            if result[0:2]=="01":
                histogram[int(result[2:], 2)] = counts.get(result)    

        return {"basis_vec": job.basis_vec, "histogram": histogram, "total": total}


class HHLSimulatedBenchmark(HHLBenchmarkBase):
    """
    Simulated HHL Benchmark

    The device behaves like a statevector_simulator, i.e. without noise
    """

#TODO not implemented
