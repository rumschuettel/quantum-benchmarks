import itertools as it
from functools import reduce

import numpy as np
from qiskit import QuantumCircuit

from libbench.ibm import Job as IBMJob
from .divide_and_conquer import divide_and_conquer
from .Shende_Bullock_Markov import Shende_Bullock_Markov
from .Bergholm_Vartiainen_Mottonen_Salomaa import Bergholm_Vartiainen_Mottonen_Salomaa


class IBMLineDrawingJob(IBMJob):
    @staticmethod
    def job_factory(
        points,
        num_shots,
        add_measurements,
        state_preparation_method,
        tomography_method,
        num_repetitions,
    ):
        assert tomography_method in ["custom", "GKKT"]

        n = int(np.log2(len(points)))

        for j in range(num_repetitions):
            for pauli_string in it.product(["X", "Y", "Z"], repeat=n):
                if tomography_method == "custom" and pauli_string.count("Z") < n - 1:
                    continue
                yield IBMLineDrawingJob(
                    points, num_shots, add_measurements, state_preparation_method, j, pauli_string
                )

    def __init__(
        self,
        points,
        num_shots,
        add_measurements,
        state_preparation_method,
        repetition,
        pauli_string,
    ):
        super().__init__()

        self.points = points
        self.num_shots = num_shots
        self.add_measurements = add_measurements
        self.state_preparation_method = state_preparation_method
        self.repetition = repetition
        self.pauli_string = pauli_string

        n = int(np.log2(len(points)))

        # NOTE: This is actually the INVERSE QFT because of incompatible definitions
        Fourier_coeffs = np.fft.fft(points, norm="ortho")

        circuit = self.prepare_state(Fourier_coeffs, list(range(n)), state_preparation_method)
        self.QFT(circuit, list(range(n)))
        # NOTE: qubits is now reversed

        for i, p in enumerate(pauli_string):
            if p == "X":
                circuit.h(n - 1 - i)
            elif p == "Y":
                circuit.sdg(n - 1 - i)
                circuit.h(n - 1 - i)
        if self.add_measurements:
            circuit.measure(list(range(n - 1, -1, -1)), list(range(n)))

        # store the resulting circuit
        self.circuit = circuit

    def prepare_state(self, state, qubits, state_preparation_method):
        assert state_preparation_method in ["DC", "SBM", "SBM+GC", "BVMS"]

        n = len(qubits)

        if state_preparation_method == "DC":
            ancilla_qubits = list(range(n, 2 * n - 2))
            circuit = QuantumCircuit(len(qubits) + len(ancilla_qubits), n)
            circuit = divide_and_conquer(circuit, qubits, ancilla_qubits, state)
        elif state_preparation_method == "SBM":
            circuit = QuantumCircuit(n, n)
            circuit = Shende_Bullock_Markov(circuit, qubits, state, False, True)
        elif state_preparation_method == "SBM+GC":
            circuit = QuantumCircuit(n, n)
            circuit = Shende_Bullock_Markov(circuit, qubits, state, True, True)
        elif state_preparation_method == "BVMS":
            circuit = QuantumCircuit(n, n)
            circuit = Bergholm_Vartiainen_Mottonen_Salomaa(circuit, qubits, state)

        return circuit

    def QFT(self, circuit, qubits):
        # NOTE: This method will reverse the order of the list of qubits,
        # rather than implementing a bunch of swaps at the end
        # Handle with care!
        for i, tq in enumerate(qubits):
            circuit.h(tq)
            for j, cq in list(enumerate(qubits))[i + 1 :]:
                circuit.crz(2 ** (-(j - i)) * np.pi, cq, tq)
                circuit.rz(2 ** (-(j - i + 1)) * np.pi, cq)
        return circuit

    def run(self, device):
        super().run(device)
        return device.execute(self.circuit, num_shots=self.num_shots)

    def __str__(self):
        if not self.add_measurements:
            return f"QiskitLineDrawingJob-{''.join(self.pauli_string)}"
        return f"QiskitLineDrawingJob-{self.repetition}-{''.join(self.pauli_string)}"
