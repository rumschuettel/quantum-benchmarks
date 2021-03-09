import numpy as np

from ..uniformly_controlled import (
    decompose_single_qubit_unitary,
    decompose_uniformly_controlled_unitaries,
)


def generate_single_qubit_circuit(circuit, qubit, U):
    _, a, b, c = decompose_single_qubit_unitary(U)
    circuit.rz(a * np.pi, qubit)
    circuit.ry(b * np.pi, qubit)
    circuit.rz(c * np.pi, qubit)
    return circuit


def fill_uniformly_controlled_circuit(circuit, cqs, tq, Gs):
    n = len(cqs)
    if n == 0:
        generate_single_qubit_circuit(circuit, tq, Gs[0])
    else:
        fill_uniformly_controlled_circuit(circuit, cqs[1:], tq, Gs[: 2 ** (n - 1)])
        circuit.cx(cqs[0], tq)
        fill_uniformly_controlled_circuit(circuit, cqs[1:], tq, Gs[2 ** (n - 1) :])
    return circuit


def generate_uniformly_controlled_circuit(circuit, cqs, tq, unitaries):
    assert len(unitaries) == 2 ** len(cqs)
    n = len(cqs)

    # Obtain the single qubit unitaries
    Gs, Rs = decompose_uniformly_controlled_unitaries(unitaries)
    assert len(Gs) == 2 ** n

    # Return the result
    return fill_uniformly_controlled_circuit(circuit, cqs, tq, Gs), Rs


if __name__ == "__main__":
    from scipy.stats import unitary_group
    from qiskit import QuantumCircuit, Aer, execute
    import itertools as it

    np.set_printoptions(linewidth=200)
    n = 2
    unitaries = [unitary_group.rvs(2) for _ in range(2 ** n)]
    qubits = list(range(n + 1))
    circuit = QuantumCircuit(n + 1)
    circuit, R = generate_uniformly_controlled_circuit(circuit, qubits[:n], qubits[-1], unitaries)
    print("Circuit:")
    print(circuit)
    print("Phases:")
    print(R)

    backend = Aer.get_backend("unitary_simulator")
    job = execute(circuit, backend)
    result = job.result()
    U = result.get_unitary(circuit)

    # Correct indexing mess
    corrected_U = np.empty(U.shape, dtype=np.complex_)
    for i, j in it.product(range(2 ** (n + 1)), repeat=2):
        corrected_U[
            int("".join(reversed(f"{i:0{n+1}b}")), 2),
            int("".join(reversed(f"{j:0{n+1}b}")), 2),
        ] = U[i][j]

    M = np.diag(R) @ corrected_U
    print("Implemented unitary:")
    print(np.round(M / np.exp(1.0j * np.angle(M[0, 0])), 3))

    full_unitary = np.zeros((2 ** (n + 1), 2 ** (n + 1)), dtype=np.complex_)
    for i, unitary in enumerate(unitaries):
        full_unitary[2 * i : 2 * i + 2, 2 * i : 2 * i + 2] = unitary
    print("Full unitary:")
    print(np.round(full_unitary / np.exp(1.0j * np.angle(full_unitary[0, 0])), 3))
    print(
        "Error:",
        np.max(
            np.abs(
                full_unitary / np.exp(1.0j * np.angle(full_unitary[0, 0]))
                - M / np.exp(1.0j * np.angle(M[0, 0]))
            )
        ),
    )
