import numpy as np
import pyquil as pq

from ..uniformly_controlled import (
    decompose_single_qubit_unitary,
    decompose_uniformly_controlled_unitaries,
)


def generate_single_qubit_circuit(U, qubit):
    _, a, b, c = decompose_single_qubit_unitary(U)
    program = pq.Program()
    program += pq.gates.RZ(a * np.pi, qubit)
    program += pq.gates.RY(b * np.pi, qubit)
    program += pq.gates.RZ(c * np.pi, qubit)
    return program


def fill_uniformly_controlled_circuit(Gs, cqs, tq):
    n = len(cqs)
    program = pq.Program()
    if n == 0:
        program += generate_single_qubit_circuit(Gs[0], tq)
    else:
        program += fill_uniformly_controlled_circuit(Gs[: 2 ** (n - 1)], cqs[1:], tq)
        program += pq.gates.CNOT(cqs[0], tq)
        program += fill_uniformly_controlled_circuit(Gs[2 ** (n - 1) :], cqs[1:], tq)
    return program


def generate_uniformly_controlled_circuit(unitaries, cqs, tq):
    assert len(unitaries) == 2 ** len(cqs)
    n = len(cqs)

    # Obtain the single qubit unitaries
    Gs, Rs = decompose_uniformly_controlled_unitaries(unitaries)
    assert len(Gs) == 2 ** n

    # Return the result
    return fill_uniformly_controlled_circuit(Gs, cqs, tq), Rs


if __name__ == "__main__":
    from scipy.stats import unitary_group
    from pyquil.quil import Pragma
    import itertools as it

    np.set_printoptions(linewidth=200)
    n = 2
    unitaries = [unitary_group.rvs(2) for _ in range(2 ** n)]
    qubits = list(range(n + 1))
    program = pq.Program()
    UCC, R = generate_uniformly_controlled_circuit(unitaries, qubits[:n], qubits[-1])
    program += UCC
    print("program:")
    print(program)
    print("Phases:")
    print(R)

    exit()

    # Correct indexing mess
    corrected_U = np.empty(U.shape, dtype=np.complex_)
    for i, j in it.product(range(2 ** (n + 1)), repeat=2):
        corrected_U[
            int("".join(reversed(f"{i:0{n+1}b}")), 2), int("".join(reversed(f"{j:0{n+1}b}")), 2),
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
