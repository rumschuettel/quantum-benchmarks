from typing import Dict, List, Union

import numpy as np

from libbench.google import Benchmark as GoogleBenchmark
from .job import GoogleMandelbrotJob
from .. import MandelbrotBenchmarkMixin


class GoogleMandelbrotBenchmarkBase(MandelbrotBenchmarkMixin, GoogleBenchmark):
    def __init__(self, add_measurements, **kwargs):
        super().__init__(**kwargs)
        self.add_measurements = add_measurements

    def get_jobs(self):
        yield from GoogleMandelbrotJob.job_factory(
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
        return "Google-Mandelbrot"


class GoogleMandelbrotBenchmark(GoogleMandelbrotBenchmarkBase):
    """
        Full SM Benchmark

        Either a cloud device, or a qasm_simulator, potentially with simulated noise
    """

    def __init__(self, **kwargs):
        kwargs.update({"add_measurements": True})
        super().__init__(**kwargs)

    def parse_result(self, job, result):
        post_selection_result = list(
            not any(outcome) for outcome in result.measurements["post_selection"]
        )
        num_post_selected = post_selection_result.count(True)
        psp = num_post_selected / self.num_shots
        z = (
            list(
                success and post_selected
                for success, post_selected in zip(
                    result.measurements["success"], post_selection_result
                )
            ).count(True)
            / num_post_selected
            if num_post_selected > 0
            else 0
        )

        return {"psp": psp, "z": z}


class GoogleMandelbrotSimulatedBenchmark(GoogleMandelbrotBenchmarkBase):
    """
        Simulated SM Benchmark

        The device behaves like a statevector_simulator, i.e. without noise
    """

    def __init__(self, *args, **kwargs):
        kwargs.update({"add_measurements": False})
        super().__init__(*args, **kwargs)

    def parse_result(self, job, result):
        psi = result.final_state

        psp = np.linalg.norm(psi[:: 2 ** (2 ** self.num_post_selections - 1)]) ** 2
        z = np.abs(psi[2 ** (2 ** self.num_post_selections - 1)]) ** 2 / psp if psp > 0 else 0

        return {"psp": psp, "z": z}
