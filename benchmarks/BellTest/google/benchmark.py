from typing import Dict, List, Union

import numpy as np

from libbench.google import Benchmark as GoogleBenchmark
from .job import GoogleBellTestJob
from .. import BellTestBenchmarkMixin


class GoogleBellTestBenchmarkBase(BellTestBenchmarkMixin, GoogleBenchmark):
    def __init__(self, add_measurements, **kwargs):
        super().__init__(**kwargs)
        self.add_measurements = add_measurements

    def get_jobs(self):
        yield from GoogleBellTestJob.job_factory(
            self.qubit_pairs_to_test, self.add_measurements, self.num_shots
        )

    def __str__(self):
        return "Google-BellTest"


class GoogleBellTestBenchmark(GoogleBellTestBenchmarkBase):
    """
    Full SM Benchmark

    Either a cloud device, or a qasm_simulator, potentially with simulated noise
    """

    def __init__(self, **kwargs):
        kwargs.update({"add_measurements": True})
        super().__init__(**kwargs)

    def parse_result(self, job, result):
        A = result.measurements["A"].T[0]
        B = result.measurements["B"].T[0]

        return {"eq": sum(A == B), "ineq": sum(A != B)}


class GoogleBellTestSimulatedBenchmark(GoogleBellTestBenchmarkBase):
    """
    Simulated SM Benchmark

    The device behaves like a statevector_simulator, i.e. without noise
    """

    def __init__(self, *args, **kwargs):
        kwargs.update({"add_measurements": False})
        super().__init__(*args, **kwargs)
