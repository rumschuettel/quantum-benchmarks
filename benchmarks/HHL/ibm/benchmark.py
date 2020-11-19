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
            self.matrix,
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

        total = 0
        histogram = [0] * 2 ** (job.num_qubits-job.num_ancillas)
        for result in counts:
            total += counts[result]
            if result[0:2]=="01":
                histogram[int(result[2:], 2)] = counts[result]           

        return {"basis_vec": job.basis_vec, "histogram": histogram, "total": total}


class HHLSimulatedBenchmark(HHLBenchmarkBase):
    """
    Simulated HHL Benchmark

    The device behaves like a statevector_simulator, i.e. without noise
    """

    def __init__(self, *args, **kwargs):
        kwargs.update({"add_measurements": False})
        super().__init__(*args, **kwargs)

    def parse_result(self, job, result):
        psi = result.get_statevector()

        used_qubits = (job.num_qubits-job.num_ancillas)        

        histogram = []
        for i in range(2 ** used_qubits):
            j = i +  2**job.num_qubits - 2**used_qubits
            histogram.append(np.abs(psi[j]) ** 2)

        return {"basis_vec": job.basis_vec, "histogram": histogram, "total": 1}
