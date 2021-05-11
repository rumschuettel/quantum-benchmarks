import itertools as it
from functools import reduce

import numpy as np
import cirq

from libbench.google import Job as GoogleJob

from .. import BellTestType


class GoogleBellTestJob(GoogleJob):
    @staticmethod
    def job_factory(qubit_pairs, add_measurements, num_shots):
        for path in qubit_pairs:
            yield GoogleBellTestJob(path, BellTestType.AB, add_measurements, num_shots)
            yield GoogleBellTestJob(path, BellTestType.AC, add_measurements, num_shots)
            yield GoogleBellTestJob(path, BellTestType.BC, add_measurements, num_shots)

    def __init__(self, path: list, test_type: BellTestType, add_measurements, num_shots):
        super().__init__()

        qubit_a = path[0]
        qubit_b = path[-1]

        self.qubit_a = qubit_a
        self.qubit_b = qubit_b
        self.path = path
        self.test_type = test_type
        self.add_measurements = add_measurements
        self.num_shots = num_shots

        # Build the circuit
        _path = [cirq.GridQubit(0, i) for i in path]
        _qubit_a, _qubit_b = _path[0], _path[-1]

        circuit = cirq.Circuit()

        circuit.append(cirq.X(_qubit_a))
        circuit.append(cirq.X(_qubit_b))
        circuit.append(cirq.H(_qubit_a))

        # CNOT along path
        for (_x, _y) in zip(_path[:-2], _path[1:-1]):
            circuit.append(cirq.H(_y))
            circuit.append(cirq.CZ(_x, _y))
            circuit.append(cirq.H(_y))

        # CNOT the last pair
        circuit.append(cirq.H(_qubit_b))
        circuit.append(cirq.CZ(_qubit_a, _qubit_b))
        circuit.append(cirq.H(_qubit_b))

        # undo CNOT along path
        for (_x, _y) in reversed(list(zip(_path[:-2], _path[1:-1]))):
            circuit.append(cirq.H(_y))
            circuit.append(cirq.CZ(_x, _y))
            circuit.append(cirq.H(_y))

        # measurement directions
        angle_a, angle_b = test_type.value
        if angle_a != 0:
            circuit.append(cirq.Rz(angle_a)(_qubit_a))
        if angle_b != 0:
            circuit.append(cirq.Rz(angle_b)(_qubit_b))

        # final hadamards
        circuit.append(cirq.H(_qubit_a))
        circuit.append(cirq.H(_qubit_b))

        # measurements
        if add_measurements:
            circuit.append(cirq.measure(_qubit_a, key="A"))
            circuit.append(cirq.measure(_qubit_b, key="B"))

        # store the resulting circuit
        self.circuit = circuit

    def run(self, device):
        super().run(device)
        return device.execute(self.circuit, num_shots=self.num_shots)

    def __str__(self):
        return f"CirqBellTestJob--{self.qubit_a}-{self.qubit_b}-{self.test_type}"
