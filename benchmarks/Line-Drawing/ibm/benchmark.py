from typing import Dict, List

import numpy as np

from libbench.ibm import Benchmark as IBMBenchmark

from .job import IBMLineDrawingJob
from .. import LineDrawingBenchmarkMixin


class IBMLineDrawingBenchmarkBase(LineDrawingBenchmarkMixin, IBMBenchmark):
    def __init__(self, add_measurements, **kwargs):
        super().__init__(**kwargs)
        self.add_measurements = add_measurements

    def get_jobs(self):
        yield from IBMLineDrawingJob.job_factory(
            self.points,
            self.num_shots,
            self.add_measurements,
            self.state_preparation_method,
            self.tomography_method,
            self.num_repetitions,
        )

    def __str__(self):
        return f"Qiskit-Line-Drawing--{self.shape}-{len(self.points)}"


class IBMLineDrawingBenchmark(IBMLineDrawingBenchmarkBase):
    """
    Full Line Drawing Benchmark

    Either a cloud device, or a qasm_simulator, potentially with simulated noise
    """

    def __init__(self, **kwargs):
        kwargs.update({"add_measurements": True})
        super().__init__(**kwargs)

    def parse_result(self, job, result):
        n = int(np.log2(len(self.points)))
        assert len(self.points) == 2 ** n

        hist = result.get_counts()
        corrected_hist = {}
        for i in range(2 ** n):
            s = f"{i:0{n}b}"
            corrected_hist["".join(reversed(s))] = hist[s] / self.num_shots if s in hist else 0
        return corrected_hist


class IBMLineDrawingSimulatedBenchmark(IBMLineDrawingBenchmarkBase):
    """
    Simulated Line Drawing Benchmark

    The device behaves like a statevector_simulator, i.e. without noise
    """

    def __init__(self, **kwargs):
        kwargs.update({"add_measurements": False})
        super().__init__(**kwargs)

    def parse_result(self, job, result):
        n = int(np.log2(len(self.points)))
        assert len(self.points) == 2 ** n

        # NOTE: Qubits are reversed, so no need to revert again
        psi = result.get_statevector()
        psi = psi[: 2 ** n]
        corrected_psi = psi
        # corrected_psi = np.empty(psi.shape, dtype = np.complex_)
        # for i,r in enumerate(psi):
        #     corrected_psi[int(''.join(reversed(f"{i:0{n}b}")),2)] = r
        hist = {f"{i:0{n}b}": abs(corrected_psi[i]) ** 2 for i in range(2 ** n)}
        return hist
