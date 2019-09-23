from typing import Dict, List

import numpy as np

from libbench.google import Benchmark as GoogleBenchmark

from .job import GoogleSchroedingerMicroscopeJob


class GoogleSchroedingerMicroscopeBenchmarkBase(GoogleBenchmark):
    def __init__(
        self, num_post_selections, num_pixels, xmin, xmax, ymin, ymax, shots, simulation
    ):
        super().__init__()

        self.num_post_selections = num_post_selections
        self.num_pixels = num_pixels
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.shots = shots
        self.simulation = simulation

    def get_jobs(self):
        yield from GoogleSchroedingerMicroscopeJob.job_factory(
            self.num_post_selections,
            self.num_pixels,
            self.xmin,
            self.xmax,
            self.ymin,
            self.ymax,
            self.shots,
            self.simulation,
        )

    def collate_results(self, results: Dict[GoogleSchroedingerMicroscopeJob, object]):
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
            shots = shots,
            simulation = False,
        )

    def parse_result(self, job, result):
        post_selection_result = list(not any(outcome) for outcome in result.measurements['post_selection'])
        num_post_selected = post_selection_result.count(True)
        psp = num_post_selected / self.shots
        z = list(success and post_selected for success,post_selected in zip(result.measurements['success'], post_selection_result)).count(True) / num_post_selected if num_post_selected > 0 else 0

        return {"psp": psp, "z": z}


class GoogleSchroedingerMicroscopeSimulatedBenchmark(
    GoogleSchroedingerMicroscopeBenchmarkBase
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
            shots = 1,
            simulation = True,
        )

    def parse_result(self, job, result):
        psi = result.final_state

        psp = np.linalg.norm(psi[::2**(2**self.num_post_selections-1)])**2
        z = np.abs(psi[2**(2**self.num_post_selections-1)])**2 / psp if psp > 0 else 0

        return {"psp": psp, "z": z}
