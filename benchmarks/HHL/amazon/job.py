import itertools as it
from functools import reduce

import numpy as np
from math import pi
from numpy import arccos, sqrt
import random as random

# For nice printing during debug
from pandas import DataFrame

from braket.circuits import Circuit

from libbench.amazon import Job as AmazonJob

from .. import HHLBenchmarkMixin
from .. import matrices


class HHLJob(AmazonJob):
    @staticmethod
    def create_qsvt_circuit(num_qubits, num_ancillas, add_measurements, block_encoding, block_encoding_inv, angles):
        qsvt_circuit = Circuit()
        if num_ancillas != 1:
            raise NotImplementedError("The general QSVT circuit generation is not yet implemented!")
        else:
            qubits = list(range(1, num_qubits + 1))

            # Quanutm Singular Value Transformation
            qsvt_circuit.h(0)
            for i in range(0, len(angles)):
                if i % 2 == 0:
                    qsvt_circuit.add_circuit(block_encoding, qubits=qubits)
                else:
                    qsvt_circuit.add_circuit(block_encoding_inv, qubits=qubits)
                # qsvt_circuit.x(1)
                qsvt_circuit.cnot(1, 0)
                qsvt_circuit.rz(0, -2 * angles[i])
                # For debugging purposes to get the global phase right replace the above line with the following:
                # qsvt_circuit.u1(-angles[i],0)
                # qsvt_circuit.x(0)
                # qsvt_circuit.u1(angles[i],0)
                # qsvt_circuit.x(0)
                qsvt_circuit.cnot(1, 0)
                # qsvt_circuit.x(1)
            qsvt_circuit.h(0)

            return qsvt_circuit

    @staticmethod
    def list_to_circuit(circuit_list: list, circuit: Circuit) -> Circuit:

        gate_lut = {
            "H": lambda index: circuit.h(index),                 
            "X": lambda index: circuit.x(index),
            "Y": lambda index: circuit.y(index),
            "Z": lambda index: circuit.z(index),
            "R": lambda index: circuit.rz(index, 2 * np.pi / 3),       
            "S": lambda index: circuit.s(index),
            "T": lambda index: circuit.t(index),
            "RX": lambda index: circuit.rx(index, 2 * np.pi / 3),  
            "SX": lambda index: circuit.rx(index, np.pi / 2),  
            "TX": lambda index: circuit.rx(index, np.pi / 4),
            "RY": lambda index: circuit.ry(index, 2 * np.pi / 3),              
            "SY": lambda index: circuit.ry(index, np.pi / 2),
            "TY": lambda index: circuit.ry(index, np.pi / 4),
            "CX": lambda control, target: circuit.cx(control, target),
            "CZ": lambda qubit1, qubit2: circuit.cz(qubit1, qubit2),    
            # TODO: Define the gate below   
            # "SQSWAP": lambda qubit1, qubit2: circuit.append(SwapGate().power(0.5), [qubit1, qubit2])   
        }

        for gate, *indices in circuit_list:
            gate_lut[gate](*[ idx - 1 for idx in indices ])

        return circuit

    @staticmethod
    def job_factory(
        matrix,
        num_shots,
        shots_multiplier,
        add_measurements,
    ):
        if matrix is None:
            raise NotImplementedError("The matrix is Not specified")
        num_qubits = matrix["qubits"]
        num_ancillas = matrix["ancillas"]

        if num_ancillas != 1:
            raise NotImplementedError("The general HHL circuit generation is not yet implemented!")

        # Build block-encoding of A
        block_encoding = Circuit()
        HHLJob.list_to_circuit(matrix["circuit"], block_encoding)
        # block_encoding.draw()

        # Angles describing the polynomial inverting A
        angles= matrix["angles"]

        # Quanutm Singular Value Transformation
        qsvt_circuit = HHLJob.create_qsvt_circuit(
            num_qubits,
            num_ancillas,
            add_measurements,
            block_encoding.adjoint(),
            block_encoding,
            angles,
        )

        # For debug purposes
        # reorder = QuantumCircuit(num_qubits+1)
        # reorder.swap(0,3)
        # reorder.swap(1,2)

        # Debugging the circuit
        # print(block_encoding)
        # print_unitary=reorder.compose(block_encoding,qubits=list(range(1,num_qubits + 1))).extend(reorder)
        # #job execution and getting the unitary matrix of the circuit
        # job = execute(print_unitary, BasicAer.get_backend('unitary_simulator'))
        # print(DataFrame(job.result().get_unitary(print_unitary, decimals=2)))

        #raise NotImplementedError("Stop now")

        # Debugging the circuit
        # print(qsvt_circuit)
        # print_unitary=reorder.combine(qsvt_circuit).extend(reorder)
        # # job execution and getting the unitary matrix of the circuit
        # job = execute(print_unitary, BasicAer.get_backend('unitary_simulator'))
        # print(DataFrame(job.result().get_unitary(print_unitary, decimals=2)))

        used_qubits = num_qubits - num_ancillas

        for m_idx in range(shots_multiplier):
            for basis_vec in range(0, 2 ** used_qubits):
                instance_circuit = Circuit()
                # Here we assume that there is a single ancilla
                instance_circuit.x(1)
                for i in range(used_qubits):
                    if basis_vec % 2 ** (i+1) >= 2 ** i:
                        instance_circuit.x(num_qubits-i)
                instance_circuit.add_circuit(qsvt_circuit)

                yield HHLJob(
                    instance_circuit,
                    num_qubits,
                    num_ancillas,
                    basis_vec,
                    num_shots,
                    m_idx,
                    add_measurements,
                )

    def __init__(
        self,
        circuit,
        num_qubits,
        num_ancillas,
        basis_vec,
        shots,
        m_idx,
        add_measurements,
    ):
        super().__init__()

        self.circuit = circuit
        self.num_qubits = num_qubits
        self.num_ancillas = num_ancillas
        self.basis_vec = basis_vec
        self.shots = shots
        self.m_idx = m_idx
        self.add_measurements = add_measurements     

    def run(self, device):
        super().run(device)
        return device.execute(self.circuit, num_shots=self.shots)

    def __str__(self):
        return f"AmazonHHLJob--{self.num_qubits-self.num_ancillas}-{self.basis_vec}-{self.shots}-{self.m_idx}"
