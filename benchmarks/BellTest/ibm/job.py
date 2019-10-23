import itertools as it
from functools import reduce

import numpy as np
from qiskit import QuantumCircuit, execute

from libbench.ibm import Job as IBMJob


class IBMBellTestJob(IBMJob):
    @staticmethod
    def job_factory(qubit_pairs, add_measurements, num_shots):
        for (a, b) in qubit_pairs:
            yield IBMBellTestJob(a, b, add_measurements, num_shots)

    def __init__(self, qubit_a, qubit_b, add_measurements, num_shots):
        super().__init__()

        self.qubit_a = qubit_a
        self.qubit_b = qubit_b
        self.add_measurements = add_measurements
        self.num_shots = num_shots

        # Set up the circuit
        circuit = QuantumCircuit(2, 2) if add_measurements else QuantumCircuit(2)

        # store the resulting circuit
        self.circuit = circuit

    def run(self, device):
        return execute(self.circuit, device, shots=self.num_shots)

    def __str__(self):
        return f"IBMBellTestJob-{self.qubit_a}-{self.qubit_b}"
