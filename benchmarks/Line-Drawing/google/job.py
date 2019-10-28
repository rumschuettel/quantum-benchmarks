import itertools as it
from functools import reduce

from typing import Union

import numpy as np
import cirq

from libbench.google import Job as GoogleJob
from .divide_and_conquer import divide_and_conquer
from .Shende_Bullock_Markov import Shende_Bullock_Markov
from .Bergholm_Vartiainen_Mottonen_Salomaa import Bergholm_Vartiainen_Mottonen_Salomaa


class GoogleLineDrawingJob(GoogleJob):
    @staticmethod
    def job_factory(
        points,
        num_shots,
        add_measurements,
        state_prepartion_method,
        num_repetitions
    ):
        n = int(np.log2(len(points)))
        assert len(points) == 2**n
        assert abs(np.linalg.norm(points) - 1.) < 1e-4

        for j in range(num_repetitions):
            yield GoogleLineDrawingJob(points, num_shots, add_measurements, state_prepartion_method, j)
            for i in range(n):
                yield GoogleLineDrawingJob(points, num_shots, add_measurements, state_prepartion_method, j, Hadamard_qubit = i)
                yield GoogleLineDrawingJob(points, num_shots, add_measurements, state_prepartion_method, j, Hadamard_qubit = i, S_qubit = i)

    def __init__(self, points, num_shots, add_measurements, state_prepartion_method, repetition, Hadamard_qubit = None, S_qubit = None):
        super().__init__()

        self.points = points
        self.num_shots = num_shots
        self.add_measurements = add_measurements
        self.state_prepartion_method = state_prepartion_method
        self.repetition = repetition
        self.Hadamard_qubit = Hadamard_qubit
        self.S_qubit = S_qubit

        n = int(np.log2(len(points)))
        assert len(points) == 2**n
        assert abs(np.linalg.norm(points) - 1.) < 1e-4

        Fourier_coeffs = np.fft.fft(points, norm = 'ortho')

        qubits = [cirq.GridQubit(0,i) for i in range(n)]
        circuit = cirq.Circuit()
        circuit.append(self.prepare_state(Fourier_coeffs, qubits, state_prepartion_method))
        circuit.append(self.QFT(qubits))
        # NOTE: qubits is now reversed

        if S_qubit != None:
            circuit.append(cirq.S(qubits[S_qubit]))
        if Hadamard_qubit != None:
            circuit.append(cirq.H(qubits[Hadamard_qubit]))
        if add_measurements:
            circuit.append(cirq.measure(*qubits, key = "result"))

        # store the resulting circuit
        self.qubits = qubits
        self.circuit = circuit

        # Display some statistics
        qubit_ops = [len(op.qubits) for moment in circuit for op in moment]
        print(" - No. single qubit gates:", qubit_ops.count(1))
        print(" - No. two qubit gates:", qubit_ops.count(2))

    def prepare_state(self, state, qubits, method):
        assert method in ['DC', 'SBM', 'SBM+GC', 'BVMS']

        n = int(np.log2(len(state)))
        assert len(state) == 2**n
        assert abs(np.linalg.norm(state) - 1.) < 1e-4

        qubits = [cirq.GridQubit(0,i) for i in range(n)]
        circuit = cirq.Circuit()
        if method == 'DC':
            ancilla_qubits = [cirq.GridQubit(1,i) for i in range(n-2)]
            circuit.append(divide_and_conquer(state, qubits, ancilla_qubits))
        elif method == 'SBM':
            circuit.append(Shende_Bullock_Markov(state, qubits, False, True))
        elif method == 'SBM+GC':
            circuit.append(Shende_Bullock_Markov(state, qubits, True, True))
        elif method == 'BVMS':
            circuit.append(Bergholm_Vartiainen_Mottonen_Salomaa(state, qubits))
        return circuit

    def QFT(self, qubits):
        # NOTE: This method will reverse the order of the list of qubits,
        # rather than implementing a bunch of swaps at the end
        # Handle with care!
        circuit = cirq.Circuit()
        for i,tq in enumerate(qubits):
            circuit.append(cirq.H(tq))
            for j,cq in list(enumerate(qubits))[i+1:]:
                circuit.append(cirq.CZ(cq,tq)**(2**(-(j-i))))
        qubits.reverse()
        return circuit

    def run(self, device):
        super().run(device)
        kwargs = {}
        if not self.add_measurements:
            kwargs['qubit_order'] = self.qubits + list(set(self.circuit.all_qubits()).difference(self.qubits))
        return device.execute(self.circuit, num_shots = self.num_shots, **kwargs)

    def __str__(self):
        if not self.add_measurements:
            return "GoogleLineDrawingJob"
        else:
            return f"GoogleLineDrawingJob-{self.repetition}-{self.Hadamard_qubit}-{self.S_qubit}"
