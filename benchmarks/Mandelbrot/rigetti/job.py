import itertools as it
from functools import reduce
from typing import Union

import numpy as np
import pyquil as pq
from pyquil.quil import Pragma

from libbench.rigetti import Job as RigettiJob


class RigettiMandelbrotJob(RigettiJob):
    @staticmethod
    def job_factory(num_post_selections, num_pixels, xmin, xmax, ymin, ymax, shots):
        xs = np.linspace(xmin, xmax, num_pixels + 1)
        xs = 0.5 * (xs[:-1] + xs[1:])
        ys = np.linspace(ymin, ymax, num_pixels + 1)
        ys = 0.5 * (ys[:-1] + ys[1:])

        for (i, x), (j, y) in it.product(enumerate(xs), enumerate(ys)):
            z = x + 1j * y
            yield RigettiMandelbrotJob(num_post_selections, z, i, j, shots)

    def __init__(self, num_post_selections, z, i, j, shots):
        super().__init__()

        self.num_post_selections = num_post_selections
        self.z = z
        self.i = i
        self.j = j
        self.shots = shots

        # Calculate the required circuit parameters
        r2 = abs(z) * np.sqrt(1 + .5*np.sqrt(1 + 4/abs(z)**2))
        r1 = 1/r2
        phi = np.angle(z)
        r1rot = -2*np.arccos(1/np.sqrt(1.+r1**2))
        r2rot = -2*np.arccos(1/np.sqrt(1.+r2**2))

        # Build the circuit
        program = pq.Program()
        program += Pragma('INITIAL_REWIRING', ['"GREEDY"'])

        qubits = 2 ** num_post_selections
        for k in range(2**num_post_selections):
            program += pq.gates.X(k)

        for k in range(1,num_post_selections+1):
            for l in range(0,2**num_post_selections,2**k):
                program += pq.gates.CNOT(l, l + 2 ** (k - 1))
                program += pq.gates.H(l).controlled(l + 2 ** (k - 1))
                program += pq.gates.RY(r1rot, l + 2 ** (k - 1)).controlled(l)
                program += pq.gates.CZ(l, l + 2 ** (k - 1))
                program += pq.gates.RZ(phi, l)
                program += pq.gates.RZ(-phi, l + 2 ** (k - 1))
                program += pq.gates.X(l + 2 ** (k - 1))
                program += pq.gates.RY(r2rot, l).controlled(l + 2 ** (k - 1))
                program += pq.gates.CZ(l, l + 2 ** (k - 1))
                program += pq.gates.CNOT(l, l + 2 ** (k - 1))
                program += pq.gates.X(l + 2 ** (k - 1))

        # store the resulting circuit
        self.program = program

    def run(self, device):
        return device.execute(self.program, num_shots=self.shots)

    def __str__(self):
        return f"RigettiMandelbrotJob-{self.i}-{self.j}"
