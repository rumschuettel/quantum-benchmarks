import numpy as np

from libbench.rigetti import Benchmark as RigettiBenchmark

from .job import HHLJob
from .. import HHLBenchmarkMixin


class HHLBenchmarkBase(HHLBenchmarkMixin, RigettiBenchmark):
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
        return "Rigetti-HHL"


class HHLBenchmark(HHLBenchmarkBase):
    """
    Full Benchmark

    Either a cloud device, or a qasm_simulator, potentially with simulated noise
    """

    def __init__(self, *args, **kwargs):
        kwargs.update({"add_measurements": True})
        super().__init__(*args, **kwargs)

    def parse_result(self, job, result):
        counts = {}
        qubits = job.num_qubits + job.num_ancillas + 1
        for measurement in np.vstack([result[k] for k in range(qubits)]).T:
            key = "".join(["0" if b == 0 else "1" for b in measurement])
            if key in counts:
                counts[key] += 1
            else:
                counts[key] = 1

        histogram = [0] * 2 ** job.num_qubits
        for result in counts:
            if int(result, 2) < 2 ** job.num_qubits:
                histogram[int(result, 2)] = counts[result]

        return {"basis_vec": job.basis_vec, "histogram": histogram}


class HHLSimulatedBenchmark(HHLBenchmarkBase):
    """
    Simulated HHL Benchmark

    The device behaves like a statevector_simulator, i.e. without noise
    """

    def __init__(self, *args, **kwargs):
        kwargs.update({"add_measurements": False})
        super().__init__(*args, **kwargs)

    def parse_result(self, job, result):
        psi = result.amplitudes

        histogram = []
        for i in range(2 ** job.num_qubits):
            j = int(format(i, f"0{2*job.num_qubits}b")[::-1], 2)
            histogram.append(np.abs(psi[j]) ** 2)

        return {"basis_vec": job.basis_vec, "histogram": histogram}
