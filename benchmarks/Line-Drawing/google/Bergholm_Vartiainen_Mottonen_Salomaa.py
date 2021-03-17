import numpy as np
import cirq
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
    circuit = cirq.Circuit()
    if n > 1:
        circuit.append(Bergholm_Vartiainen_Mottonen_Salomaa(nullified_state, qubits[:-1]))
    circuit.append(cirq.inverse(UCC))
    return circuit


if __name__ == "__main__":

    n = 2
    state = np.random.rand(2 ** n) + 1.0j * np.random.rand(2 ** n)
    state /= np.linalg.norm(state)
    qubits = [cirq.GridQubit(0, i) for i in range(n)]
    circuit = Bergholm_Vartiainen_Mottonen_Salomaa(state, qubits)
    result = cirq.Simulator().simulate(circuit, qubit_order=qubits).final_state_vector

    # Statistics
    np.set_printoptions(linewidth=200)
    print("State to prepare:", np.round(state, 4))
    print("Norm:", np.linalg.norm(state))
    print("Circuit:")
    print(circuit)
    print("State that was prepared:", np.round(result, 4))
    print("Norm of the resulting vector:", np.linalg.norm(result))
    print("Inner product error:", abs(abs(np.sum(np.conj(result) * state)) - 1.0))
