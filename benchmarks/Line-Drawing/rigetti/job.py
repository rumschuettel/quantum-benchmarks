import itertools as it
from functools import reduce

import numpy as np
import pyquil as pq
from pyquil.quil import Pragma

from libbench.rigetti import Job as RigettiJob
from .divide_and_conquer import divide_and_conquer
from .Shende_Bullock_Markov import Shende_Bullock_Markov
from .Bergholm_Vartiainen_Mottonen_Salomaa import Bergholm_Vartiainen_Mottonen_Salomaa


class RigettiLineDrawingJob(RigettiJob):
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
                yield RigettiLineDrawingJob(
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

        program = pq.Program()
        program += Pragma("INITIAL_REWIRING", ['"GREEDY"'])

        program += self.prepare_state(Fourier_coeffs, list(range(n)), state_preparation_method)
        program += self.QFT(list(range(n)))
        # NOTE: qubits is now reversed

        for i, p in enumerate(pauli_string):
            if p == "X":
                program += pq.gates.H(n - 1 - i)
            elif p == "Y":
                program += pq.gates.S(n - 1 - i).dagger()
                program += pq.gates.H(n - 1 - i)

        # store the resulting program
        self.program = program

    def prepare_state(self, state, qubits, method):
        assert method in ["DC", "SBM", "SBM+GC", "BVMS"]

        n = len(qubits)

        if method == "DC":
            ancilla_qubits = list(range(n, 2 * n - 2))
            return divide_and_conquer(state, qubits, ancilla_qubits)
        elif method == "SBM":
            return Shende_Bullock_Markov(state, qubits, False, True)
        elif method == "SBM+GC":
            return Shende_Bullock_Markov(state, qubits, True, True)
        elif method == "BVMS":
            return Bergholm_Vartiainen_Mottonen_Salomaa(state, qubits)

    def QFT(self, qubits):
        # NOTE: This method will reverse the order of the list of qubits,
        # rather than implementing a bunch of swaps at the end
        # Handle with care!
        program = pq.Program()
        for i, tq in enumerate(qubits):
            program += pq.gates.H(tq)
            for j, cq in list(enumerate(qubits))[i + 1 :]:
                program += pq.gates.RZ(2 ** (-(j - i)) * np.pi, tq).controlled(cq)
                program += pq.gates.RZ(2 ** (-(j - i + 1)) * np.pi, cq)
        return program

    def run(self, device):
        super().run(device)
        return device.execute(self.program, num_shots=self.num_shots)

    def __str__(self):
        if not self.add_measurements:
            return f"RigettiLineDrawingJob-{''.join(self.pauli_string)}"
        return f"RigettiLineDrawingJob-{self.repetition}-{''.join(self.pauli_string)}"
