import itertools as it
from functools import reduce

import numpy as np
from math import pi
from numpy import arccos, sqrt
import random as random

# For nice printing during debug
from pandas import DataFrame

import pyquil as pq
from pyquil.quil import Program

from libbench.rigetti import Job as RigettiJob

from .. import HHLBenchmarkMixin
from .. import matrices


class HHLJob(RigettiJob):
    @staticmethod
    def create_qsvt_circuit(num_qubits, num_ancillas, block_encoding, block_encoding_inv, angles):
        qsvt_circuit = pq.Program()

        if num_ancillas != 1:
            raise NotImplementedError("The general QSVT circuit generation is not yet implemented!")
        else:
            # Quanutm Singular Value Transformation
            qsvt_circuit += pq.gates.H(0)
            for i in range(0, len(angles)):
                if i % 2 == 0:
                    qsvt_circuit += block_encoding  # Not at the correct qubits!
                else:
                    qsvt_circuit += block_encoding_inv  # Not at the correct qubits!
                qsvt_circuit += pq.gates.CNOT(1, 0)
                qsvt_circuit += pq.gates.RZ(-2 * angles[i], 0)
                qsvt_circuit += pq.gates.CNOT(1, 0)
            qsvt_circuit += pq.gates.H(0)

            return qsvt_circuit

    @staticmethod
    def list_to_circuit(circuit_list: list, circuit: Program) -> Program:

        gate_lut = {
            "H": lambda index: pq.gates.H(index),
            "X": lambda index: pq.gates.X(index),
            "Y": lambda index: pq.gates.Y(index),
            "Z": lambda index: pq.gates.Z(index),
            "R": lambda index: pq.gates.RZ(2 * np.pi / 3, index),
            "S": lambda index: pq.gates.S(index),
            "T": lambda index: pq.gates.T(index),
            "RX": lambda index: pq.gates.RX(2 * np.pi / 3, index),
            "SX": lambda index: pq.gates.RX(np.pi / 2, index),
            "TX": lambda index: pq.gates.RX(np.pi / 4, index),
            "RY": lambda index: pq.gates.RY(2 * np.pi / 3, index),
            "SY": lambda index: pq.gates.RY(np.pi / 2, index),
            "TY": lambda index: pq.gates.RY(np.pi / 4, index),
            "CX": lambda control, target: pq.gates.CNOT(control, target),
            "CZ": lambda qubit1, qubit2: pq.gates.CZ(qubit1, qubit2),
            # TODO: Define the gate below
            # "SQSWAP": lambda qubit1, qubit2: ircuit += pq.gates.SWAP(qubit1, qubit2).power(0.5)
        }

        for gate, *indices in circuit_list:
            circuit += gate_lut[gate](*[idx for idx in indices])

        return circuit

    @staticmethod
    def job_factory(matrix, num_shots, shots_multiplier):
        if matrix is None:
            raise NotImplementedError("The matrix is Not specified")
        num_qubits = matrix["qubits"]
        num_ancillas = matrix["ancillas"]

        if num_ancillas != 1:
            raise NotImplementedError("The general HHL circuit generation is not yet implemented!")

        # Build block-encoding of A
        block_encoding = pq.Program()
        HHLJob.list_to_circuit(matrix["circuit"], block_encoding)
        # block_encoding.draw()

        # Angles describing the polynomial inverting A
        angles = matrix["angles"]

        # Quanutm Singular Value Transformation
        qsvt_circuit = HHLJob.create_qsvt_circuit(
            num_qubits, num_ancillas, block_encoding.dagger(), block_encoding, angles
        )

        used_qubits = num_qubits - num_ancillas

        for m_idx in range(shots_multiplier):
            for basis_vec in range(2 ** used_qubits):
                instance_circuit = pq.Program()

                instance_circuit += pq.gates.X(1)
                for i in range(used_qubits):
                    if basis_vec % 2 ** (i + 1) >= 2 ** i:
                        instance_circuit += pq.gates.X(num_qubits - i)

                instance_circuit += qsvt_circuit

                yield HHLJob(
                    instance_circuit, num_qubits, num_ancillas, basis_vec, num_shots, m_idx
                )

    def __init__(self, circuit, num_qubits, num_ancillas, basis_vec, shots, m_idx):
        super().__init__()

        self.circuit = circuit
        self.num_qubits = num_qubits
        self.num_ancillas = num_ancillas
        self.basis_vec = basis_vec
        self.shots = shots
        self.m_idx = m_idx

    def run(self, device):
        super().run(device)
        return device.execute(self.circuit, num_shots=self.shots)

    def __str__(self):
        return f"RigettiHHLJob--{self.num_qubits-self.num_ancillas}-{self.basis_vec}-{self.shots}-{self.m_idx}"
