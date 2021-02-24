import numpy as np
import pyquil as pq
from .uniformly_controlled_circuits import generate_uniformly_controlled_circuit


def normalize_and_remove_phase(v):
    return v / np.linalg.norm(v) / np.exp(1.0j * np.angle(v[0]))


def Bergholm_Vartiainen_Mottonen_Salomaa(state, qubits):
    assert len(state) == 2 ** len(qubits)
    n = len(qubits)

    # Generate uniformly controlled unitary and nullified state
    nullified_state = np.zeros(2 ** (n - 1), dtype=np.complex_)
    unitaries = []
    for i in range(2 ** (n - 1)):
        s = state[2 * i : 2 * i + 2]
        r = np.linalg.norm(s)
        nullified_state[i] = r
        unitaries.append(
            np.conj(np.array([[s[0] / r, -np.conj(s[1] / r)], [s[1] / r, np.conj(s[0] / r)]])).T
            if r > 1e-8
            else np.eye(2)
        )

    # Generate uniformly controlled circuit
    UCC, R = generate_uniformly_controlled_circuit(unitaries, qubits[:-1], qubits[-1])

    # Correct for phases
    nullified_state /= R[::2]

    # Merge everything into one circuit
    program = pq.Program()
    if n > 1:
        program += Bergholm_Vartiainen_Mottonen_Salomaa(nullified_state, qubits[:-1])
    program += UCC.dagger()
    return program


if __name__ == "__main__":
    from pyquil.quil import Pragma

    n = 2
    state = normalize_and_remove_phase(np.random.rand(2 ** n) + 1.0j * np.random.rand(2 ** n))
    state /= np.linalg.norm(state)
    qubits = list(range(n))
    program = pq.Program()
    program += Bergholm_Vartiainen_Mottonen_Salomaa(points, qubits)
    psi = pq.api.WavefunctionSimulator().wavefunction(program).amplitudes
    result = psi[: 2 ** n] / np.exp(1.0j * np.angle(psi[0]))

    # Revert the ordering of the qubits
    corrected_result = np.empty(result.shape, dtype=np.complex64)
    for i, r in enumerate(result):
        corrected_result[int("".join(reversed(f"{i:0{n}b}")), 2)] = r

    # Statistics
    np.set_printoptions(linewidth=200)
    print("State to prepare:", np.round(state, 4))
    print("Norm:", np.linalg.norm(state))
    print("Program:")
    print(program)
    print("State that was prepared:", np.round(corrected_result, 4))
    print("Norm of the resulting vector:", np.linalg.norm(corrected_result))
    print(
        "Inner product error:", abs(abs(np.sum(np.conj(corrected_result) * state)) - 1.0),
    )
