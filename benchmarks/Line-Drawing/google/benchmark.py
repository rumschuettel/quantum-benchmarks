from typing import Dict, List, Union

import numpy as np

from libbench.google import Benchmark as GoogleBenchmark
from .job import GoogleLineDrawingJob
from .. import LineDrawingBenchmarkMixin


class GoogleLineDrawingBenchmarkBase(
    LineDrawingBenchmarkMixin, GoogleBenchmark
):
    def __init__(self, add_measurements, **kwargs):
        super().__init__(**kwargs)
        self.add_measurements = add_measurements

    def get_jobs(self):
        yield from GoogleLineDrawingJob.job_factory(
            self.points,
            self.num_shots,
            self.add_measurements,
            self.state_prepartion_method
        )

    def __str__(self):
        return f"Google-Line-Drawing-{self.filename}"


class GoogleLineDrawingBenchmark(GoogleLineDrawingBenchmarkBase):
    """
        Full Line Drawing benchmark

        Either a cloud device, or a qasm_simulator, potentially with simulated noise
    """

    def __init__(self, **kwargs):
        kwargs.update({"add_measurements": True})
        super().__init__(**kwargs)

    def parse_result(self, job, result):
        n = len(job.qubits)
        measurements = result.measurements['result']
        str_measurements = [''.join(map(lambda x : str(int(x)), r)) for r in measurements]
        hist = {f'{i:0{n}b}' : str_measurements.count(f'{i:0{n}b}') / job.num_shots for i in range(2**n)}
        return hist


class GoogleLineDrawingSimulatedBenchmark(
    GoogleLineDrawingBenchmarkBase
):
    """
        Simulated Line Drawing benchmark

        The device behaves like a statevector_simulator, i.e. without noise
    """

    def __init__(self, *args, **kwargs):
        kwargs.update({"add_measurements": False})
        super().__init__(*args, **kwargs)

    def parse_result(self, job, result):
        n = len(job.qubits)
        psi = result.final_state
        hist = {f'{i:0{n}b}' : abs(psi[i])**2 for i in range(2**n)}
        return hist
