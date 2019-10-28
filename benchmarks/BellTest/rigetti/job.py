import itertools as it
from functools import reduce

import numpy as np
import pyquil as pq
from pyquil.quil import Pragma

from libbench.rigetti import Job as RigettiJob

from .. import BellTestType


class RigettiBellTestJob(RigettiJob):
    @staticmethod
    def job_factory(qubit_pairs, add_measurements, num_shots):
        for path in qubit_pairs:
            yield RigettiBellTestJob(path, BellTestType.AB, add_measurements, num_shots)
            yield RigettiBellTestJob(path, BellTestType.AC, add_measurements, num_shots)
            yield RigettiBellTestJob(path, BellTestType.BC, add_measurements, num_shots)

    def __init__(
        self, path: list, test_type: BellTestType, add_measurements, num_shots
    ):
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
        program = pq.Program()
        program += Pragma("INITIAL_REWIRING", ['"NAIVE"'])

        program += pq.gates.X(qubit_a)
        program += pq.gates.X(qubit_b)
        program += pq.gates.H(qubit_a)

        # SWAP's along path
        for x, y in list(zip(path[:-1], path[1:]))[:-1]:
            program += pq.gates.SWAP(x, y)

        # CNOT the last pair
        program += pq.gates.CNOT(path[-2], qubit_b)

        # SWAP's back
        for x, y in reversed(list(zip(path[:-1], path[1:]))[:-1]):
            program += pq.gates.SWAP(x, y)

        # measurement directions
        angle_a, angle_b = test_type.value
        if angle_a != 0:
            program += pq.gates.RZ(angle_a, qubit_a)
        if angle_b != 1:
            program += pq.gates.RZ(angle_b, qubit_b)

        # final hadamards
        program += pq.gates.H(qubit_a)
        program += pq.gates.H(qubit_b)

        # store the resulting circuit
        self.program = program

    def run(self, device):
        super().run(device)
        return device.execute(self.program, num_shots=self.num_shots)

    def __str__(self):
        return f"RigettiBellTestJob-{self.qubit_a}-{self.qubit_b}"
