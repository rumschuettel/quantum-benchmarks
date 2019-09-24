from typing import Dict, List

import numpy as np

from libbench.ibm import Benchmark as IBMBenchmark

from .job import IBMSchroedingerMicroscopeJob


class IBMSchroedingerMicroscopeBenchmarkBase(IBMBenchmark):
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
    ):
        super().__init__()

        self.num_post_selections = num_post_selections
        self.num_pixels = num_pixels
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.shots = shots
        self.add_measurements = add_measurements

    def get_jobs(self):
        yield from IBMSchroedingerMicroscopeJob.job_factory(
            self.num_post_selections,
            self.num_pixels,
            self.xmin,
            self.xmax,
            self.ymin,
            self.ymax,
            self.shots,
            self.add_measurements,
        )

    def collate_results(self, results: Dict[IBMSchroedingerMicroscopeJob, object]):
        # get array dimensions right
        xs = np.linspace(self.xmin, self.xmax, self.num_pixels + 1)
        xs = 0.5 * (xs[:-1] + xs[1:])
        ys = np.linspace(self.ymin, self.ymax, self.num_pixels + 1)

        # output arrays
        zs = np.empty((len(xs), len(ys)), dtype=np.float64)
        psps = np.empty((len(xs), len(ys)), dtype=np.float64)

        # fill in with values from jobs
        for job in results:
            result = results[job]

            zs[job.j, job.i] = result["z"]
            psps[job.j, job.i] = result["psp"]

        return zs, psps


class IBMSchroedingerMicroscopeBenchmark(IBMSchroedingerMicroscopeBenchmarkBase):
    """
        Full SM Benchmark

        Either a cloud device, or a qasm_simulator, potentially with simulated noise
    """

    def __init__(
        self,
        num_post_selections=1,
        num_pixels=4,
        xmin=-2,
        xmax=2,
        ymin=-2,
        ymax=2,
        shots=100,
    ):
        super().__init__(
            num_post_selections,
            num_pixels,
            xmin,
            xmax,
            ymin,
            ymax,
            shots,
            add_measurements=True,
        )

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
        psp = num_post_selected / self.shots
        z = (
            num_post_selected_successes / num_post_selected
            if num_post_selected > 0
            else 0
        )

        return {"psp": psp, "z": z}


class IBMSchroedingerMicroscopeSimulatedBenchmark(
    IBMSchroedingerMicroscopeBenchmarkBase
):
    """
        Simulated SM Benchmark

        The device behaves like a statevector_simulator, i.e. without noise
    """

    def __init__(
        self, num_post_selections=1, num_pixels=4, xmin=-2, xmax=2, ymin=-2, ymax=2
    ):
        super().__init__(
            num_post_selections,
            num_pixels,
            xmin,
            xmax,
            ymin,
            ymax,
            shots=1,
            add_measurements=False,
        )

    def parse_result(self, job, result):
        psi = result.get_statevector()

        psp = np.linalg.norm(psi[:2]) ** 2
        z = np.abs(psi[1]) ** 2 / psp if psp > 0 else 0

        return {"psp": psp, "z": z}
