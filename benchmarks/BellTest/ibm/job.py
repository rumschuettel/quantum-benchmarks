import itertools as it
from functools import reduce

import numpy as np
from qiskit import QuantumCircuit

from libbench.ibm import Job as IBMJob

from .. import BellTestType


class IBMBellTestJob(IBMJob):
    @staticmethod
    def job_factory(qubit_pairs, add_measurements, num_shots):
        for path in qubit_pairs:
            yield IBMBellTestJob(path, BellTestType.AB, add_measurements, num_shots)
            yield IBMBellTestJob(path, BellTestType.AC, add_measurements, num_shots)
            yield IBMBellTestJob(path, BellTestType.BC, add_measurements, num_shots)

    def __init__(self, path: list, test_type: BellTestType, add_measurements, num_shots):
        super().__init__()
        assert len(path) >= 2, "qubit path has to have length at least 2"

        qubit_a = path[0]
        qubit_b = path[-1]

        self.qubit_a = qubit_a
        self.qubit_b = qubit_b
        self.path = path
        self.test_type = test_type
        self.add_measurements = add_measurements
        self.num_shots = num_shots

        # Build the circuit
        # in qiskit, we cannot directly specify the target qubits;
        # this will be done in the transpiler pass for which we
        # will provide the map [0, ..., len(path)-1] -> path.
        # because we do not want to do the swaps manually, we trust in the compiler
        # to do so by disabling the optimization

        _qubit_a = 0
        _qubit_b = 1

        circuit = QuantumCircuit(2, 2) if add_measurements else QuantumCircuit(2)

        circuit.x(_qubit_a)
        circuit.x(_qubit_b)
        circuit.h(_qubit_a)

        # CNOT the last pair
        circuit.cx(_qubit_a, _qubit_b)

        # measurement directions
        angle_a, angle_b = test_type.value
        if angle_a != 0:
            circuit.rz(angle_a, _qubit_a)
        if angle_b != 1:
            circuit.rz(angle_b, _qubit_b)

        # final hadamards
        circuit.h(_qubit_a)
        circuit.h(_qubit_b)

        # measurements
        if add_measurements:
            circuit.measure([_qubit_a, _qubit_b], [0, 1])

        # store the resulting circuit
        self.circuit = circuit

    def run(self, device):
        super().run(device)
        return device.execute(
            self.circuit,
            num_shots=self.num_shots,
            initial_layout=[self.path[0], self.path[-1]],
            optimization_level=0,
        )

    def __str__(self):
        return f"IBMBellTestJob--{self.qubit_a}-{self.qubit_b}-{self.test_type}"
