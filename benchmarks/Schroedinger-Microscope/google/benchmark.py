from typing import Dict, List, Union

import numpy as np

from libbench.google import Benchmark as GoogleBenchmark
from libbench.google import Promise as GooglePromise
from libbench.google import LocalPromise as GoogleLocalPromise

from .job import GoogleSchroedingerMicroscopeJob
from .. import SchroedingerMicroscopeBenchmarkMixin


class GoogleSchroedingerMicroscopeBenchmarkBase(
    SchroedingerMicroscopeBenchmarkMixin, GoogleBenchmark
):
    def __init__(
        self,
        num_post_selections,
        num_pixels,
        xmin,
        xmax,
        ymin,
        ymax,
        shots,
        add_measurements,
        promise_type: Union[GooglePromise, GoogleLocalPromise],
    ):
        super().__init__(num_post_selections, num_pixels, xmin, xmax, ymin, ymax, shots)

        self.add_measurements = add_measurements
        self.promise_type = promise_type

    def get_jobs(self):
        yield from GoogleSchroedingerMicroscopeJob.job_factory(
            self.num_post_selections,
            self.num_pixels,
            self.xmin,
            self.xmax,
            self.ymin,
            self.ymax,
            self.shots,
            self.add_measurements,
            self.promise_type,
        )


class GoogleSchroedingerMicroscopeBenchmark(GoogleSchroedingerMicroscopeBenchmarkBase):
    """
        Full SM Benchmark

        Either a cloud device, or a qasm_simulator, potentially with simulated noise
    """

    def __init__(
        self, num_post_selections=1, num_pixels=4, xmin=-2, xmax=2, ymin=-2, ymax=2, shots=100
    ):
        super().__init__(
            num_post_selections,
            num_pixels,
            xmin,
            xmax,
            ymin,
            ymax,
            shots=shots,
            add_measurements=True,
            promise_type=GooglePromise,
        )

    def parse_result(self, job, result):
        post_selection_result = list(
            not any(outcome) for outcome in result.measurements["post_selection"]
        )
        num_post_selected = post_selection_result.count(True)
        psp = num_post_selected / self.shots
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


class GoogleSchroedingerMicroscopeSimulatedBenchmark(GoogleSchroedingerMicroscopeBenchmarkBase):
    """
        Simulated SM Benchmark

        The device behaves like a statevector_simulator, i.e. without noise
    """

    def __init__(self, num_post_selections=1, num_pixels=4, xmin=-2, xmax=2, ymin=-2, ymax=2):
        super().__init__(
            num_post_selections,
            num_pixels,
            xmin,
            xmax,
            ymin,
            ymax,
            shots=float("Inf"),
            add_measurements=False,
            promise_type=GoogleLocalPromise,
        )

    def parse_result(self, job, result):
        psi = result.final_state

        psp = np.linalg.norm(psi[:: 2 ** (2 ** self.num_post_selections - 1)]) ** 2
        z = np.abs(psi[2 ** (2 ** self.num_post_selections - 1)]) ** 2 / psp if psp > 0 else 0

        return {"psp": psp, "z": z}
