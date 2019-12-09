from typing import Dict, List

import numpy as np

from libbench.rigetti import Benchmark as RigettiBenchmark

from .job import RigettiLineDrawingJob
from .. import LineDrawingBenchmarkMixin


class RigettiLineDrawingBenchmarkBase(LineDrawingBenchmarkMixin, RigettiBenchmark):
    def __init__(self, add_measurements, **kwargs):
        super().__init__(**kwargs)
        self.add_measurements = add_measurements

    def get_jobs(self):
        yield from RigettiLineDrawingJob.job_factory(
            self.points,
            self.num_shots,
            self.add_measurements,
            self.state_preparation_method,
            self.tomography_method,
            self.num_repetitions,
        )

    def __str__(self):
        return f"Rigetti-Line-Drawing--{self.shape}-{len(self.points)}"


class RigettiLineDrawingBenchmark(RigettiLineDrawingBenchmarkBase):
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

        hist = {}
        for measurement in np.vstack([result[k] for k in range(n)]).T:
            key = "".join(["0" if b == 0 else "1" for b in measurement])
            if key in hist:
                hist[key] += 1
            else:
                hist[key] = 1

        corrected_hist = {}
        for i in range(2 ** n):
            s = f"{i:0{n}b}"
            corrected_hist["".join(reversed(s))] = hist[s] / self.num_shots if s in hist else 0
        return corrected_hist


class RigettiLineDrawingSimulatedBenchmark(RigettiLineDrawingBenchmarkBase):
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
        psi = result.amplitudes
        psi = psi[: 2 ** n]
        corrected_psi = psi
        # corrected_psi = np.empty(psi.shape, dtype = np.complex_)
        # for i,r in enumerate(psi):
        #     corrected_psi[int(''.join(reversed(f"{i:0{n}b}")),2)] = r
        hist = {f"{i:0{n}b}": abs(corrected_psi[i]) ** 2 for i in range(2 ** n)}
        return hist
