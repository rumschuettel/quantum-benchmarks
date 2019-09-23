import itertools as it
from functools import reduce

import numpy as np
import cirq

from libbench.google import Job as GoogleJob
from libbench.google import LOCAL_DEVICES as GOOGLE_LOCAL_DEVICES
from libbench.google import Promise as GooglePromise
from libbench.google import LocalPromise as GoogleLocalPromise


class GoogleSchroedingerMicroscopeJob(GoogleJob):
    @staticmethod
    def job_factory(
        num_post_selections, num_pixels, xmin, xmax, ymin, ymax, shots, simulation
    ):
        xs = np.linspace(xmin, xmax, num_pixels + 1)
        xs = 0.5 * (xs[:-1] + xs[1:])
        ys = np.linspace(ymin, ymax, num_pixels + 1)
        ys = 0.5 * (ys[:-1] + ys[1:])

        for (i, x), (j, y) in it.product(enumerate(xs), enumerate(ys)):
            z = x + 1j * y
            yield GoogleSchroedingerMicroscopeJob(
                num_post_selections, z, simulation, i, j, shots
            )

    def __init__(self, num_post_selections, z, simulation, i, j, shots):
        super().__init__()

        self.num_post_selections = num_post_selections
        self.simulation = simulation
        self.z = z
        self.i = i
        self.j = j
        self.shots = shots

        # Calculate some parameters
        theta = 2 * np.arccos(abs(z) / np.sqrt(1 + abs(z) ** 2))
        phi = np.angle(z)

        # Build the circuit
        qubits = [cirq.GridQubit(0,i) for i in range(2**num_post_selections)]
        circuit = cirq.Circuit()
        for k in range(2**num_post_selections):
            circuit.append(cirq.Ry(theta)(qubits[k]))
            circuit.append(cirq.Rz(-phi)(qubits[k]))
        for k in range(num_post_selections):
            for l in range(0,2**num_post_selections,2**(k+1)):
                circuit.append(cirq.CNOT(qubits[l], qubits[l + 2**k]))
                circuit.append([cirq.S(qubits[l]), cirq.H(qubits[l]), cirq.S(qubits[l])])
        if not simulation:
            circuit.append(cirq.measure(*(qubits[k] for k in range(1,2**num_post_selections)), key = 'post_selection'))
            circuit.append(cirq.measure(qubits[0], key = 'success'))

        # store the resulting circuit
        self.circuit = circuit

    def run(self, device, **kwargs):
        kwargs.update({'simulation' : self.simulation})

        if isinstance(device,GOOGLE_LOCAL_DEVICES):
            return GoogleLocalPromise(self.circuit, device, repetitions = self.shots, **kwargs)
        else:
            return GooglePromise(self.circuit, device, repetitions = self.shots, **kwargs)

    def __str__(self):
        return f"GoogleSchroedingerMicroscopeJob-{self.i}-{self.j}"
