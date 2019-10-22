from typing import Dict, List

import numpy as np

from libbench.ibm import Benchmark as IBMBenchmark

from .job import IBMMandelbrotJob
from .. import MandelbrotBenchmarkMixin


class IBMMandelbrotBenchmarkBase(MandelbrotBenchmarkMixin, IBMBenchmark):
    def __init__(self, add_measurements, **kwargs):
        super().__init__(**kwargs)
        self.add_measurements = add_measurements

    def get_jobs(self):
        yield from IBMMandelbrotJob.job_factory(
            self.num_post_selections,
            self.num_pixels,
            self.num_shots,
            self.xmin,
            self.xmax,
            self.ymin,
            self.ymax,
            self.add_measurements,
        )

    def __str__(self):
        return "IBM-Mandelbrot"


class IBMMandelbrotBenchmark(IBMMandelbrotBenchmarkBase):
    """
        Full SM Benchmark

        Either a cloud device, or a qasm_simulator, potentially with simulated noise
    """

    def __init__(self, **kwargs):
        kwargs.update({"add_measurements": True})
        super().__init__(**kwargs)

    def parse_result(self, job, result):
        counts = result.get_counts()

        failure_post_process_key = "0" * (2 ** self.num_post_selections - 1) + "0"
        success_post_process_key = "0" * (2 ** self.num_post_selections - 1) + "1"
        num_post_selected_failures = (
            counts[failure_post_process_key]
            if failure_post_process_key in counts
            else 0
        )
        num_post_selected_successes = (
            counts[success_post_process_key]
            if success_post_process_key in counts
            else 0
        )
        num_post_selected = num_post_selected_failures + num_post_selected_successes
        psp = num_post_selected / self.num_shots
        z = (
            num_post_selected_successes / num_post_selected
            if num_post_selected > 0
            else 0
        )

        return {"psp": psp, "z": z}


class IBMMandelbrotSimulatedBenchmark(IBMMandelbrotBenchmarkBase):
    """
        Simulated SM Benchmark

        The device behaves like a statevector_simulator, i.e. without noise
    """

    def __init__(self, **kwargs):
        kwargs.update({"add_measurements": False})
        super().__init__(**kwargs)

    def parse_result(self, job, result):
        psi = result.get_statevector()

        psp = np.linalg.norm(psi[:2]) ** 2
        z = np.abs(psi[1]) ** 2 / psp if psp > 0 else 0

        return {"psp": psp, "z": z}
