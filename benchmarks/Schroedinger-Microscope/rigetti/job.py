import itertools as it
from functools import reduce
from typing import Union

import numpy as np
import pyquil as pq

from libbench.rigetti import Job as RigettiJob

from libbench.rigetti import Promise as RigettiPromise
from libbench.rigetti import LocalPromise as RigettiLocalPromise


class RigettiSchroedingerMicroscopeJob(RigettiJob):
    @staticmethod
    def job_factory(
        num_post_selections, num_pixels, xmin, xmax, ymin, ymax, shots,
        promise_type: Union[RigettiPromise, RigettiLocalPromise]
    ):
        xs = np.linspace(xmin, xmax, num_pixels + 1)
        xs = 0.5 * (xs[:-1] + xs[1:])
        ys = np.linspace(ymin, ymax, num_pixels + 1)
        ys = 0.5 * (ys[:-1] + ys[1:])

        for (i, x), (j, y) in it.product(enumerate(xs), enumerate(ys)):
            z = x + 1j * y
            yield RigettiSchroedingerMicroscopeJob(
                num_post_selections, z, i, j, shots, promise_type
            )

    def __init__(self, num_post_selections, z, i, j, shots,
        promise_type: Union[RigettiPromise, RigettiLocalPromise]
        ):
        super().__init__()

        self.num_post_selections = num_post_selections
        self.z = z
        self.i = i
        self.j = j
        self.shots = shots
        self.promise_type = promise_type

        # Calculate some parameters
        theta = 2 * np.arccos(abs(z) / np.sqrt(1 + abs(z) ** 2))
        phi = np.angle(z)

        program = pq.Program()
        qubits = 2 ** num_post_selections
        
        for k in range(qubits):
            program += pq.gates.RY(theta, k)
            program += pq.gates.RZ(-phi, k)

        for k in range(num_post_selections):
            for l in range(0, qubits, 2 ** (k + 1)):
                program += pq.gates.CNOT(l, l + 2 ** k)
                program += pq.gates.S(l)
                program += pq.gates.H(l)
                program += pq.gates.S(l)

        # store the resulting circuit
        self.program = program

    def run(self, device, *args, **kwargs):
        kwargs.update({ "trials": self.shots })
        return self.promise_type(self.program, device, *args, **kwargs)

    def __str__(self):
        return f"RigettiSchroedingerMicroscopeJob-{self.i}-{self.j}"
