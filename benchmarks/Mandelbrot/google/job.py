import itertools as it
from functools import reduce

from typing import Union

import numpy as np
import cirq

from libbench.google import Job as GoogleJob


class GoogleMandelbrotJob(GoogleJob):
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
            yield GoogleMandelbrotJob(num_post_selections, num_shots, z, add_measurements, i, j)

    def __init__(self, num_post_selections, num_shots, z, add_measurements, i, j):
        super().__init__()

        self.num_post_selections = num_post_selections
        self.num_shots = num_shots
        self.add_measurements = add_measurements
        self.z = z
        self.i = i
        self.j = j

        # Calculate the required circuit parameters
        r2 = abs(z) * np.sqrt(1 + 0.5 * np.sqrt(1 + 4 / abs(z) ** 2))
        r1 = 1 / r2
        phi = np.angle(z)
        r1rot = -2 * np.arccos(1 / np.sqrt(1.0 + r1 ** 2))
        r2rot = -2 * np.arccos(1 / np.sqrt(1.0 + r2 ** 2))

        # Build the circuit
        qubits = [cirq.GridQubit(0, i) for i in range(2 ** num_post_selections)]
        circuit = cirq.Circuit()
        for k in range(2 ** num_post_selections):
            circuit.append(cirq.X(qubits[k]))
        for k in range(1, num_post_selections + 1):
            for l in range(0, 2 ** num_post_selections, 2 ** k):
                circuit.append(cirq.CNOT(qubits[l], qubits[l + 2 ** (k - 1)]))
                circuit.append(cirq.H(qubits[l]).controlled_by(qubits[l + 2 ** (k - 1)]))
                circuit.append(cirq.Ry(r1rot)(qubits[l + 2 ** (k - 1)]).controlled_by(qubits[l]))
                circuit.append(cirq.CZ(qubits[l], qubits[l + 2 ** (k - 1)]))
                circuit.append(cirq.Rz(phi)(qubits[l]))
                circuit.append(cirq.Rz(-phi)(qubits[l + 2 ** (k - 1)]))
                circuit.append(cirq.X(qubits[l + 2 ** (k - 1)]))
                circuit.append(cirq.Ry(r2rot)(qubits[l]).controlled_by(qubits[l + 2 ** (k - 1)]))
                circuit.append(cirq.CZ(qubits[l], qubits[l + 2 ** (k - 1)]))
                circuit.append(cirq.CNOT(qubits[l], qubits[l + 2 ** (k - 1)]))
                circuit.append(cirq.X(qubits[l + 2 ** (k - 1)]))
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
        return f"GoogleMandelbrotJob-{self.i}-{self.j}"
