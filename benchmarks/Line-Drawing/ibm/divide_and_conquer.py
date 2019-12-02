import numpy as np


def normalize_and_remove_phase(v):
    return v / np.linalg.norm(v) / np.exp(1.0j * np.angle(v[0]))


def optimize_toffoli(circuit, a, b, c):
    circuit.h(c)
    circuit.tdg(c)
    circuit.cx(a, c)
    circuit.t(c)
    circuit.cx(b, c)
    circuit.tdg(c)
    circuit.cx(a, c)
    circuit.t(c)
    circuit.h(c)
    return circuit


def divide_and_conquer(circuit, qubits, ancilla_qubits, points, ctrl=None):
    n = int(np.log2(len(points)))
    assert len(points) == 2 ** n

    points = normalize_and_remove_phase(points)
    assert abs(np.linalg.norm(points) - 1.0) < 1e-4
    assert abs(np.angle(points[0])) < 1e-4

    p1 = np.linalg.norm(points[: 2 ** (n - 1)])
    theta = 2 * np.arccos(p1) / np.pi
    phi = np.angle(points[2 ** (n - 1)]) / np.pi

    if abs(theta) > 1e-4:
        if ctrl is not None:
            circuit.cu3(theta * np.pi, 0, 0, ctrl, qubits[0])
        else:
            circuit.ry(theta * np.pi, qubits[0])
        # if ctrl is not None: circuit.rz(-.5 * np.pi * theta, ctrl)

    if abs(phi) > 1e-4:
        if ctrl is not None:
            circuit.crz(phi * np.pi, ctrl, qubits[0])
        else:
            circuit.rz(phi * np.pi, qubits[0])
        if ctrl is not None:
            circuit.rz(0.5 * phi * np.pi, ctrl)

    if n > 1:
        one_part = points[2 ** (n - 1) :]
        zero_part = points[: 2 ** (n - 1)]

        if np.linalg.norm(one_part) < 1e-4:
            divide_and_conquer(circuit, qubits[1:], ancilla_qubits[1:], zero_part, ctrl)
        elif np.linalg.norm(zero_part) < 1e-4:
            divide_and_conquer(circuit, qubits[1:], ancilla_qubits[1:], one_part, ctrl)
        else:
            new_qubits = qubits[1:]
            if ctrl is not None:
                new_ctrl = ancilla_qubits[0]
                new_ancilla_qubits = ancilla_qubits[1:]
                # circuit.append(cirq.CCX(ctrl,qubits[0],new_ctrl))
                optimize_toffoli(circuit, ctrl, qubits[0], new_ctrl)
            else:
                new_ctrl = qubits[0]
                new_ancilla_qubits = ancilla_qubits
            divide_and_conquer(
                circuit, new_qubits, new_ancilla_qubits, points[2 ** (n - 1) :], new_ctrl
            )
            if ctrl is not None:
                circuit.cx(ctrl, new_ctrl)
            else:
                circuit.x(new_ctrl)
            divide_and_conquer(
                circuit, new_qubits, new_ancilla_qubits, points[: 2 ** (n - 1)], new_ctrl
            )
            if ctrl is not None:
                circuit.cx(ctrl, new_ctrl)
                # circuit.append(cirq.CCX(ctrl, qubits[0], new_ctrl))

                # This is a symmetric circuit, so no need to invert
                optimize_toffoli(circuit, ctrl, qubits[0], new_ctrl)
            else:
                circuit.x(new_ctrl)
    return circuit


if __name__ == "__main__":
    from qiskit import QuantumCircuit, execute, Aer

    n = 2
    state = np.random.rand(2 ** n) + 1.0j * np.random.rand(2 ** n)
    state /= np.linalg.norm(state)
    qubits = list(range(n))
    ancilla_qubits = list(range(n, 2 * n - 2))
    circuit = QuantumCircuit(len(qubits) + len(ancilla_qubits))
    divide_and_conquer(circuit, qubits, ancilla_qubits, state)
    backend = Aer.get_backend("statevector_simulator")
    psi = execute(circuit, backend).result().get_statevector()
    result = psi[: 2 ** n] / np.exp(1.0j * np.angle(psi[0]))

    # Revert the ordering of the qubits
    corrected_result = np.empty(result.shape, dtype=np.complex64)
    for i, r in enumerate(result):
        corrected_result[int("".join(reversed(f"{i:0{n}b}")), 2)] = r

    # Statistics
    np.set_printoptions(linewidth=200)
    print("State to prepare:", np.round(state,4))
    print("Norm:", np.linalg.norm(state))
    print("Circuit:")
    print(circuit)
    print("State that was prepared:", np.round(corrected_result,4))
    print("Norm of the resulting vector:", np.linalg.norm(corrected_result))
    print("Inner product error:", abs(abs(np.sum(np.conj(corrected_result) * state)) - 1.0))
