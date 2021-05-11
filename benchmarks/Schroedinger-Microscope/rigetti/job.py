import itertools as it
from functools import reduce
from typing import Union

import numpy as np
import pyquil as pq
from pyquil.quil import Pragma

from libbench.rigetti import Job as RigettiJob


class RigettiSchroedingerMicroscopeJob(RigettiJob):
    @staticmethod
    def job_factory(num_post_selections, num_pixels, xmin, xmax, ymin, ymax, shots):
        xs = np.linspace(xmin, xmax, num_pixels + 1)
        xs = 0.5 * (xs[:-1] + xs[1:])
        ys = np.linspace(ymin, ymax, num_pixels + 1)
        ys = 0.5 * (ys[:-1] + ys[1:])

        for (i, x), (j, y) in it.product(enumerate(xs), enumerate(ys)):
            z = x + 1j * y
            yield RigettiSchroedingerMicroscopeJob(num_post_selections, z, i, j, shots)

    def __init__(self, num_post_selections, z, i, j, shots):
        super().__init__()

        self.num_post_selections = num_post_selections
        self.z = z
        self.i = i
        self.j = j
        self.shots = shots

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

    def run(self, device):
        super().run(device)
        return device.execute(self.program, num_shots=self.shots)

    def __str__(self):
        return f"ForestSchroedingerMicroscopeJob-{self.i}-{self.j}"
