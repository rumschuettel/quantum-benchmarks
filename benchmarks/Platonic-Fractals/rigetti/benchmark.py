import numpy as np

from libbench.rigetti import Benchmark as RigettiBenchmark

from .job import RigettiPlatonicFractalsJob
from .. import PlatonicFractalsBenchmarkMixin


class RigettiPlatonicFractalsBenchmarkBase(PlatonicFractalsBenchmarkMixin, RigettiBenchmark):
    def __init__(self, add_measurements, **kwargs):
        super().__init__(**kwargs)

        self.add_measurements = add_measurements

    def get_jobs(self):
        yield from RigettiPlatonicFractalsJob.job_factory(
            self.body,
            self.strength,
            self.num_steps,
            self.num_shots,
            self.shots_multiplier,
            self.add_measurements,
        )

    def __str__(self):
        return "Forest-PlatonicFractals"


class RigettiPlatonicFractalsBenchmark(RigettiPlatonicFractalsBenchmarkBase):
    """
    Full Benchmark
    """

    def __init__(self, *args, **kwargs):
        kwargs.update({"add_measurements": True})
        super().__init__(*args, **kwargs)

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
        qubits = len(job.meas_dirs) + 1
        for measurement in np.vstack([result[k] for k in range(qubits)]).T:
            key = "".join(["0" if b == 0 else "1" for b in measurement])
            if key in counts:
                counts[key] += 1
            else:
                counts[key] = 1

        if self.body != 0:  # PlatonicFractalsBenchmarkMixin.BODY_OCTA
            raise NotImplementedError("This fractal has not been implemented")

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


class RigettiPlatonicFractalsSimulatedBenchmark(RigettiPlatonicFractalsBenchmarkBase):
    """
    Simulated Benchmark

    The device behaves like a statevector_simulator, i.e. without noise
    """

    def __init__(self, *args, **kwargs):
        kwargs.update({"add_measurements": False})
        super().__init__(*args, **kwargs)
        raise NotImplementedError()
