import itertools as it
from functools import reduce

import numpy as np
from qiskit import QuantumCircuit, execute

from libbench.ibm import Job as IBMJob


class IBMPlatonicFractalsJob(IBMJob):
    @staticmethod
    def job_factory(
        num_post_selections, num_pixels, xmin, xmax, ymin, ymax, shots, add_measurements
    ):
        xs = np.linspace(xmin, xmax, num_pixels + 1)
        xs = 0.5 * (xs[:-1] + xs[1:])
        ys = np.linspace(ymin, ymax, num_pixels + 1)
        ys = 0.5 * (ys[:-1] + ys[1:])

        for (i, x), (j, y) in it.product(enumerate(xs), enumerate(ys)):
            z = x + 1j * y
            yield IBMPlatonicFractalsJob(
                num_post_selections, z, add_measurements, i, j, shots
            )

    def __init__(self, num_post_selections, z, add_measurements, i, j, shots):
        super().__init__()

        self.num_post_selections = num_post_selections
        self.add_measurements = add_measurements
        self.z = z
        self.i = i
        self.j = j
        self.shots = shots

        # Calculate some parameters
        theta = 2 * np.arccos(abs(z) / np.sqrt(1 + abs(z) ** 2))
        phi = np.angle(z)

        # Build the circuit
        circuit = (
            QuantumCircuit(2 ** num_post_selections, 2 ** num_post_selections)
            if add_measurements
            else QuantumCircuit(2 ** num_post_selections)
        )
        for k in range(2 ** num_post_selections):
            circuit.ry(theta, k)
            circuit.rz(-phi, k)
        for k in range(num_post_selections):
            for l in range(0, 2 ** num_post_selections, 2 ** (k + 1)):
                circuit.cx(l, l + 2 ** k)
                circuit.s(l)
                circuit.h(l)
                circuit.s(l)
        if add_measurements:
            circuit.measure(
                list(range(2 ** num_post_selections)), list(range(2 ** num_post_selections))
            )

        # store the resulting circuit
        self.circuit = circuit

    def run(self, device, *args, **kwargs):
        return execute(self.circuit, device, shots=self.shots)

    def __str__(self):
        return f"IBMPlatonicFractalsJob-{self.i}-{self.j}"
