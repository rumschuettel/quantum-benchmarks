from typing import Dict, List

import numpy as np

from libbench.rigetti import Benchmark as RigettiBenchmark

from .job import RigettiBellTestJob
from .. import BellTestBenchmarkMixin


class RigettiBellTestBenchmarkBase(BellTestBenchmarkMixin, RigettiBenchmark):
    def __init__(self, add_measurements, **kwargs):
        super().__init__(**kwargs)
        self.add_measurements = add_measurements

    def get_jobs(self):
        yield from RigettiBellTestJob.job_factory(
            self.qubit_pairs_to_test, self.add_measurements, self.num_shots
        )

    def __str__(self):
        return "Rigetti-BellTest"


class RigettiBellTestBenchmark(RigettiBellTestBenchmarkBase):
    """
        Full SM Benchmark

        Either a cloud device, or a qasm_simulator, potentially with simulated noise
    """

    def __init__(self, **kwargs):
        kwargs.update({"add_measurements": True})
        super().__init__(**kwargs)

    def parse_result(self, job, result):
        """
        initially results are in the form qubit : measurement-outcomes
        {
            0: array([1, 0, 0, 1, 1, 1, 1, 0, 1, 0]),
            1: array([1, 0, 1, 1, 1, 0, 1, 0, 1, 0]),
            2: array([1, 0, 0, 1, 1, 1, 1, 0, 1, 0])
        }
        so each column represents one joint measurement outcome; selecting only a subset of the qubits
        effectively means measuring only a subset, ignoring the rest
        """

        equal_outcomes = result[job.qubit_a] == result[job.qubit_b]

        return {"eq": equal_outcomes.sum(), "ineq": (~equal_outcomes).sum()}


class RigettiBellTestSimulatedBenchmark(RigettiBellTestBenchmarkBase):
    """
        Simulated SM Benchmark

        The device behaves like a statevector_simulator, i.e. without noise
    """

    def __init__(self, **kwargs):
        kwargs.update({"add_measurements": False})
        super().__init__(**kwargs)

    def parse_result(self, job, result):
        psi = result.get_statevector()

        raise NotImplementedError()
