from typing import Dict, List, Union

import numpy as np

from libbench.rigetti import Benchmark as RigettiBenchmark
from libbench.rigetti import LocalPromise as RigettiLocalPromise
from libbench.rigetti import Promise as RigettiPromise

from .job import RigettiSchroedingerMicroscopeJob
from .. import SchroedingerMicroscopeBenchmarkMixin


class RigettiSchroedingerMicroscopeBenchmarkBase(
    SchroedingerMicroscopeBenchmarkMixin, RigettiBenchmark
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
        promise_type: Union[RigettiPromise, RigettiLocalPromise],
        **kwargs
    ):
        super().__init__(num_post_selections, num_pixels, xmin, xmax, ymin, ymax, shots)

        self.promise_type = promise_type

    def get_jobs(self):
        yield from RigettiSchroedingerMicroscopeJob.job_factory(
            self.num_post_selections,
            self.num_pixels,
            self.xmin,
            self.xmax,
            self.ymin,
            self.ymax,
            self.shots,
            self.promise_type,
        )

    def __str__(self):
        return "Rigetti-Schroedinger-Microscope"


class RigettiSchroedingerMicroscopeBenchmark(RigettiSchroedingerMicroscopeBenchmarkBase):
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
            shots,
            promise_type=RigettiPromise,
        )


class RigettiSchroedingerMicroscopeSimulatedBenchmark(RigettiSchroedingerMicroscopeBenchmarkBase):
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
            shots=1,
            promise_type=RigettiLocalPromise,
        )

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
        counts = {}
        qubits = 2 ** self.num_post_selections
        for measurement in np.vstack(result[k] for k in range(qubits)).T:
            key = "".join(["0" if b == 0 else "1" for b in measurement])
            if key in counts:
                counts[key] += 1
            else:
                counts[key] = 1

        failure_post_process_key = "0" * (2 ** self.num_post_selections - 1) + "0"
        success_post_process_key = "0" * (2 ** self.num_post_selections - 1) + "1"
        num_post_selected_failures = (
            counts[failure_post_process_key] if failure_post_process_key in counts else 0
        )
        num_post_selected_successes = (
            counts[success_post_process_key] if success_post_process_key in counts else 0
        )
        num_post_selected = num_post_selected_failures + num_post_selected_successes
        psp = num_post_selected / self.shots
        z = num_post_selected_successes / num_post_selected if num_post_selected > 0 else 0

        return {"psp": psp, "z": z}
