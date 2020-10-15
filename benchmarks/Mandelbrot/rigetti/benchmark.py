from typing import Dict, List, Union

import numpy as np

from libbench.rigetti import Benchmark as RigettiBenchmark

from .job import RigettiMandelbrotJob
from .. import MandelbrotBenchmarkMixin


class RigettiMandelbrotBenchmarkBase(MandelbrotBenchmarkMixin, RigettiBenchmark):
    def get_jobs(self):
        yield from RigettiMandelbrotJob.job_factory(
            self.num_post_selections,
            self.num_pixels,
            self.xmin,
            self.xmax,
            self.ymin,
            self.ymax,
            self.num_shots,
        )

    def __str__(self):
        return "Rigetti-Mandelbrot"


class RigettiMandelbrotSimulatedBenchmark(RigettiMandelbrotBenchmarkBase):
    """
        Statevector simulator
    """
    def parse_result(self, job, result):
        psi = result.amplitudes

        psp = np.linalg.norm(psi[:2]) ** 2
        z = np.abs(psi[1]) ** 2 / psp if psp > 0 else 0

        return {"psp": psp, "z": z}


class RigettiMandelbrotBenchmark(RigettiMandelbrotBenchmarkBase):
    """
        Measure and run
    """
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
        for measurement in np.vstack([result[k] for k in range(qubits)]).T:
            key = "".join(["0" if b == 0 else "1" for b in measurement])
            if key in counts:
                counts[key] += 1
            else:
                counts[key] = 1

        failure_post_process_key = "0" + "0" * (2 ** self.num_post_selections - 1)
        success_post_process_key = "1" + "0" * (2 ** self.num_post_selections - 1)
        num_post_selected_failures = (
            counts[failure_post_process_key] if failure_post_process_key in counts else 0
        )
        num_post_selected_successes = (
            counts[success_post_process_key] if success_post_process_key in counts else 0
        )
        num_post_selected = num_post_selected_failures + num_post_selected_successes
        psp = num_post_selected / self.num_shots
        z = num_post_selected_successes / num_post_selected if num_post_selected > 0 else 0

        return {"psp": psp, "z": z}
