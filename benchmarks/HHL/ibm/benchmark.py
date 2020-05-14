import numpy as np

from libbench.ibm import Benchmark as IBMBenchmark

from .job import HHLJob
from .. import HHLBenchmarkMixin


class HHLBenchmarkBase(HHLBenchmarkMixin, IBMBenchmark):
    def __init__(self, add_measurements, **kwargs):
        super().__init__(**kwargs)

        self.add_measurements = add_measurements

    def get_jobs(self):
        yield from HHLJob.job_factory(
            self.block_encoding,
            self.num_qubits,    
            self.num_ancillas,
            self.qsvt_poly,
            self.num_shots,
            self.shots_multiplier,  
            self.add_measurements,
        )

    def __str__(self):
        return "IBM-HHL"


class HHLBenchmark(HHLBenchmarkBase):
    """
        Full Benchmark

        Either a cloud device, or a qasm_simulator, potentially with simulated noise
    """

    def __init__(self, *args, **kwargs):
        kwargs.update({"add_measurements": True})
        super().__init__(*args, **kwargs)

    def parse_result(self, job, result):
        counts = result.get_counts()

        histogram = [0] * 2**job.num_qubits
        for result in counts:
            if int(result,2) < 2**job.num_qubits:
                histogram[int(result,2)] = counts[result]

        return {
            "basis_vec": job.basis_vec,
            "histogram": histogram,
        }


class HHLSimulatedBenchmark(HHLBenchmarkBase):
    """
        Simulated HHL Benchmark

        The device behaves like a statevector_simulator, i.e. without noise
    """

    def __init__(self, *args, **kwargs):
        kwargs.update({"add_measurements": False})
        super().__init__(*args, **kwargs)
        raise NotImplementedError()
