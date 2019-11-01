from typing import Dict, List

import numpy as np

from libbench.ibm import Benchmark as IBMBenchmark

from .job import IBMBellTestJob
from .. import BellTestBenchmarkMixin


class IBMBellTestBenchmarkBase(BellTestBenchmarkMixin, IBMBenchmark):
    def __init__(self, add_measurements, **kwargs):
        super().__init__(**kwargs)
        self.add_measurements = add_measurements

    def get_jobs(self):
        yield from IBMBellTestJob.job_factory(
            self.qubit_pairs_to_test, self.add_measurements, self.num_shots
        )

    def __str__(self):
        return "IBM-BellTest"


class IBMBellTestBenchmark(IBMBellTestBenchmarkBase):
    """
        Full SM Benchmark

        Either a cloud device, or a qasm_simulator, potentially with simulated noise
    """

    def __init__(self, **kwargs):
        kwargs.update({"add_measurements": True})
        super().__init__(**kwargs)

    def parse_result(self, job, result):
        counts = result.get_counts()

        return {"eq": counts["00"] + counts["11"], "ineq": counts["01"] + counts["10"]}


class IBMBellTestSimulatedBenchmark(IBMBellTestBenchmarkBase):
    """
        Simulated SM Benchmark

        The device behaves like a statevector_simulator, i.e. without noise
    """

    def __init__(self, **kwargs):
        kwargs.update({"add_measurements": False})
        super().__init__(**kwargs)

    def parse_result(self, job, result):
        psi = result.get_statevector()

        return None
