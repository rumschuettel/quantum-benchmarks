import itertools as it
from functools import reduce

import numpy as np
from qiskit import QuantumCircuit

from libbench.ibm import Job as IBMJob


class IBMMandelbrotJob(IBMJob):
    @staticmethod
    def job_factory(
        num_post_selections, num_pixels, num_shots, xmin, xmax, ymin, ymax, add_measurements
    ):
        xs = np.linspace(xmin, xmax, num_pixels + 1)
        xs = 0.5 * (xs[:-1] + xs[1:])
        ys = np.linspace(ymin, ymax, num_pixels + 1)
        ys = 0.5 * (ys[:-1] + ys[1:])

        for (i, x), (j, y) in it.product(enumerate(xs), enumerate(ys)):
            z = x + 1j * y
            yield IBMMandelbrotJob(num_post_selections, z, add_measurements, i, j, num_shots)

    def __init__(self, num_post_selections, z, add_measurements, i, j, num_shots):
        super().__init__()

        self.num_post_selections = num_post_selections
        self.add_measurements = add_measurements
        self.z = z
        self.i = i
        self.j = j
        self.num_shots = num_shots

        # Calculate the required circuit parameters
        r2 = abs(z) * np.sqrt(1 + 0.5 * np.sqrt(1 + 4 / abs(z) ** 2))
        r1 = 1 / r2
        phi = np.angle(z)
        r1rot = -2 * np.arccos(1 / np.sqrt(1.0 + r1 ** 2))
        r2rot = -2 * np.arccos(1 / np.sqrt(1.0 + r2 ** 2))

        # Set up the circuit
        circuit = (
            QuantumCircuit(2 ** num_post_selections, 2 ** num_post_selections)
            if add_measurements
            else QuantumCircuit(2 ** num_post_selections)
        )
        for k in range(2 ** num_post_selections):
            circuit.x(k)
        for k in range(1, num_post_selections + 1):
            for l in range(0, 2 ** num_post_selections, 2 ** k):
                circuit.cx(l, l + 2 ** (k - 1))
                circuit.ch(l + 2 ** (k - 1), l)
                circuit.cu3(r1rot, 0, 0, l, l + 2 ** (k - 1))  # cu3(theta,0,0) == cry(theta)
                circuit.cz(l, l + 2 ** (k - 1))
                circuit.rz(phi, l)
                circuit.rz(-phi, l + 2 ** (k - 1))
                circuit.x(l + 2 ** (k - 1))
                circuit.cu3(r2rot, 0, 0, l + 2 ** (k - 1), l)
                circuit.cz(l, l + 2 ** (k - 1))
                circuit.cx(l, l + 2 ** (k - 1))
                circuit.x(l + 2 ** (k - 1))
        if add_measurements:
            circuit.measure(
                list(range(2 ** num_post_selections)), list(range(2 ** num_post_selections))
            )

        # store the resulting circuit
        self.circuit = circuit

    def run(self, device):
        super().run(device)
        return device.execute(self.circuit, num_shots=self.num_shots)

    def __str__(self):
        return f"IBMMandelbrotJob-{self.i}-{self.j}"
