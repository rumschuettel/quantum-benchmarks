import itertools as it
from functools import reduce

from typing import Union

import numpy as np
import cirq

from libbench.google import Job as GoogleJob


class GoogleSchroedingerMicroscopeJob(GoogleJob):
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
            yield GoogleSchroedingerMicroscopeJob(
                num_post_selections, num_shots, z, add_measurements, i, j
            )

    def __init__(self, num_post_selections, num_shots, z, add_measurements, i, j):
        super().__init__()

        self.num_post_selections = num_post_selections
        self.num_shots = num_shots
        self.add_measurements = add_measurements
        self.z = z
        self.i = i
        self.j = j

        # Calculate some parameters
        theta = 2 * np.arccos(abs(z) / np.sqrt(1 + abs(z) ** 2))
        phi = np.angle(z)

        # Build the circuit
        qubits = [cirq.GridQubit(0, i) for i in range(2 ** num_post_selections)]
        circuit = cirq.Circuit()
        for k in range(2 ** num_post_selections):
            circuit.append(cirq.Y(qubits[k]) ** (theta / np.pi))
            circuit.append(cirq.Z(qubits[k]) ** (-phi / np.pi))
        for k in range(num_post_selections):
            for l in range(0, 2 ** num_post_selections, 2 ** (k + 1)):
                circuit.append(cirq.CNOT(qubits[l], qubits[l + 2 ** k]))
                circuit.append([cirq.S(qubits[l]), cirq.H(qubits[l]), cirq.S(qubits[l])])
        if add_measurements:
            circuit.append(
                cirq.measure(
                    *(qubits[k] for k in range(1, 2 ** num_post_selections)), key="post_selection"
                )
            )
            circuit.append(cirq.measure(qubits[0], key="success"))

        # store the resulting circuit
        self.circuit = circuit

    def run(self, device):
        super().run(device)
        return device.execute(self.circuit, num_shots=self.num_shots)

    def __str__(self):
        return f"GoogleSchroedingerMicroscopeJob-{self.i}-{self.j}"
