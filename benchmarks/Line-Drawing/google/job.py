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
    def job_factory(points, num_shots, add_measurements, state_preparation_method, tomography_method, num_repetitions):
        assert tomography_method in ["custom", "GKKT"]

        n = int(np.log2(len(points)))

        for j in range(num_repetitions):
            for pauli_string in it.product(['X','Y','Z'], repeat = n):
                if tomography_method == 'custom' and pauli_string.count('Z') < n-1: continue
                yield GoogleLineDrawingJob(points, num_shots, add_measurements, state_preparation_method, j, pauli_string)

    def __init__(self, points, num_shots, add_measurements, state_preparation_method, repetition, pauli_string):
        super().__init__()

        self.points = points
        self.num_shots = num_shots
        self.add_measurements = add_measurements
        self.state_preparation_method = state_preparation_method
        self.repetition = repetition
        self.pauli_string = pauli_string

        n = int(np.log2(len(points)))

        Fourier_coeffs = np.fft.fft(points, norm="ortho")

        qubits = [cirq.GridQubit(0, i) for i in range(n)]
        circuit = cirq.Circuit()
        circuit.append(self.prepare_state(Fourier_coeffs, qubits, state_preparation_method))
        circuit.append(self.QFT(qubits))
        # NOTE: qubits is now reversed

        for p,q in zip(pauli_string, qubits):
            if p == 'X': circuit.append(cirq.H(q))
            elif p == 'Y':
                circuit.append(cirq.inverse(cirq.S(q)))
                circuit.append(cirq.H(q))
        if self.add_measurements:
            circuit.append(cirq.measure(*qubits, key = 'result'))

        # store the resulting circuit
        self.qubits = qubits
        self.circuit = circuit

        # Display some statistics
        qubit_ops = [len(op.qubits) for moment in circuit for op in moment]
        print(" - No. single qubit gates:", qubit_ops.count(1))
        print(" - No. two qubit gates:", qubit_ops.count(2))

    def prepare_state(self, state, qubits, state_preparation_method):
        assert state_preparation_method in ["DC", "SBM", "SBM+GC", "BVMS"]

        n = int(np.log2(len(state)))

        qubits = [cirq.GridQubit(0, i) for i in range(n)]
        circuit = cirq.Circuit()
        if state_preparation_method == "DC":
            ancilla_qubits = [cirq.GridQubit(1, i) for i in range(n - 2)]
            circuit.append(divide_and_conquer(state, qubits, ancilla_qubits))
        elif state_preparation_method == "SBM":
            circuit.append(Shende_Bullock_Markov(state, qubits, False, True))
        elif state_preparation_method == "SBM+GC":
            circuit.append(Shende_Bullock_Markov(state, qubits, True, True))
        elif state_preparation_method == "BVMS":
            circuit.append(Bergholm_Vartiainen_Mottonen_Salomaa(state, qubits))
        return circuit

    def QFT(self, qubits):
        # NOTE: This method will reverse the order of the list of qubits,
        # rather than implementing a bunch of swaps at the end
        # Handle with care!
        circuit = cirq.Circuit()
        for i, tq in enumerate(qubits):
            circuit.append(cirq.H(tq))
            for j, cq in list(enumerate(qubits))[i + 1 :]:
                circuit.append(cirq.CZ(cq, tq) ** (2 ** (-(j - i))))
        qubits.reverse()
        return circuit

    def run(self, device):
        super().run(device)
        kwargs = {}
        if not self.add_measurements:
            kwargs["qubit_order"] = self.qubits + list(
                set(self.circuit.all_qubits()).difference(self.qubits)
            )
        return device.execute(self.circuit, num_shots=self.num_shots, **kwargs)

    def __str__(self):
        if not self.add_measurements:
            return f"GoogleLineDrawingJob-{''.join(self.pauli_string)}"
        return f"GoogleLineDrawingJob-{self.repetition}-{''.join(self.pauli_string)}"
