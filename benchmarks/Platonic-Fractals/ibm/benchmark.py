from typing import Dict, List

import numpy as np

from libbench.ibm import Benchmark as IBMBenchmark

from .job import IBMPlatonicFractalsJob
from .. import PlatonicFractalsBenchmarkMixin


class IBMPlatonicFractalsBenchmarkBase(PlatonicFractalsBenchmarkMixin, IBMBenchmark):
    def __init__(
        self, body, strength, num_steps, num_dirs_change, num_shots, random_seed, add_measurements
    ):
        super().__init__(body, strength, num_steps, num_dirs_change, num_shots, random_seed)

        self.add_measurements = add_measurements

    def get_jobs(self):
        yield from IBMPlatonicFractalsJob.job_factory(
            self.body,
            self.strength,
            self.num_steps,
            self.num_dirs_change,
            self.num_shots,
            self.random_seed,
            self.add_measurements,
        )

    def __str__(self):
        return "IBM-Platonic-Fractals"


class IBMPlatonicFractalsBenchmark(IBMPlatonicFractalsBenchmarkBase):
    """
        Full SM Benchmark

        Either a cloud device, or a qasm_simulator, potentially with simulated noise
    """

    def __init__(
        self, body=0, strength=0.93, num_steps=2, num_dirs_change=42, num_shots=1024, random_seed=42
    ):
        super().__init__(
            body,
            strength,
            num_steps,
            num_dirs_change,
            num_shots,
            random_seed,
            add_measurements=True,
        )

    def parse_result(self, job, result):
        counts = result.get_counts()

        if self.body != 0:  # PlatonicFractalsBenchmarkMixin.BODY_OCTA
            print("This fractal is not yet implemented!")
            raise NotImplementedError

        avg = {}
        total = {}
        state = {}
        for bits in counts:
            if not bits[:-1] in total:
                total[bits[:-1]] = 0
                avg[bits[:-1]] = 0
            total[bits[:-1]] += counts[bits]
            avg[bits[:-1]] += (-2 * int(bits[-1]) + 1) * counts[bits]
        for dir in total:
            # if total[dir]>= threshold:
            state[dir] = avg[dir] / total[dir]

        if job.final_meas_dir == 2:
            return {
                "dirs": job.meas_dirs,
                "ymeascounts": total,
                "ystates": state,
            }  # collections.OrderedDict(sorted(state.items()))
        if job.final_meas_dir == 3:
            return {"dirs": job.meas_dirs, "zmeascounts": total, "zstates": state}


class IBMPlatonicFractalsSimulatedBenchmark(IBMPlatonicFractalsBenchmarkBase):
    """
        Simulated SM Benchmark

        The device behaves like a statevector_simulator, i.e. without noise
    """

    def __init__(self, body=0, strength=0.93, num_steps=2, num_dirs_change=42, random_seed=42):
        super().__init__(
            body,
            strength,
            num_steps,
            num_dirs_change,
            num_shots=1,
            random_seed=random_seed,
            add_measurements=False,
        )
        print("Not implemented yet")
        raise NotImplementedError

    def parse_result(self, job, result):  # Not implemented yet
        print("Not implemented yet")
        raise NotImplementedError
