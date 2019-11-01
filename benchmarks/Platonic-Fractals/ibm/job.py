import itertools as it
from functools import reduce

import numpy as np
from math import pi
from numpy import arccos, sqrt
import random as random
from qiskit import QuantumCircuit

from libbench.ibm import Job as IBMJob

from .. import PlatonicFractalsBenchmarkMixin


class IBMPlatonicFractalsJob(IBMJob):
    @staticmethod
    def job_factory(
        body, strength, num_steps, num_dirs_change, num_shots, random_seed, add_measurements
    ):
        random.seed(random_seed)

        for _ in range(num_dirs_change):
            dirs = []
            for _ in range(num_steps):
                dirs.append(random.randrange(1, 4))
            yield IBMPlatonicFractalsJob(body, strength, dirs, 2, num_shots, add_measurements)
            yield IBMPlatonicFractalsJob(body, strength, dirs, 3, num_shots, add_measurements)

    def __init__(self, body, strength, meas_dirs, final_meas_dir, shots, add_measurements):
        super().__init__()

        self.body = body
        self.strength = strength
        self.meas_dirs = meas_dirs
        self.final_meas_dir = final_meas_dir
        self.shots = shots
        self.add_measurements = add_measurements

        if not body == 0:  # PlatonicFractalsBenchmarkMixin.BODY_OCTA
            raise NotImplementedError("This fractal is not yet implemented!")

        # Calculate some parameters
        angle1 = arccos(sqrt((1 + strength) / 2))
        angle2 = arccos(sqrt((1 - strength) / 2))

        # Build the circuit
        circuit = (
            QuantumCircuit(len(meas_dirs) + 1, len(meas_dirs) + 1)
            if add_measurements
            else QuantumCircuit(len(meas_dirs) + 1)
        )
        circuit.h(0)
        for i in range(len(meas_dirs)):
            if meas_dirs[i] == 2:
                circuit.sdg(0)
            if meas_dirs[i] == 1 or meas_dirs[i] == 2:
                circuit.h(0)
            circuit.h(i + 1)
            circuit.rz(2 * angle1, i + 1)
            # octa.crz(2*(angle2-angle1),qubit,ancillas[i])
            circuit.crz(2 * (pi / 2 - 2 * angle1), 0, i + 1)
            circuit.h(i + 1)
            if meas_dirs[i] == 1 or meas_dirs[i] == 2:
                circuit.h(0)
            if meas_dirs[i] == 2:
                circuit.s(0)
        if final_meas_dir == 2:
            circuit.sdg(0)
        if final_meas_dir == 1 or final_meas_dir == 2:
            circuit.h(0)
        if add_measurements:
            # print(list(range(1,len(meas_dirs)+1))+[0])
            # print([len(meas_dirs)-i for i in range(len(meas_dirs)+1)])
            circuit.measure(
                list(range(1, len(meas_dirs) + 1)) + [0],
                [len(meas_dirs) - i for i in range(len(meas_dirs) + 1)],
            )
        # store the resulting circuit
        self.circuit = circuit

    def run(self, device):
        super().run(device)
        return device.execute(self.circuit, num_shots=self.shots)

    def __str__(self):
        return f"IBMPlatonicFractalsJob-{self.strength}-{self.meas_dirs}-{self.final_meas_dir}"
