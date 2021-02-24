import numpy as np
import pyquil as pq


def normalize_and_remove_phase(v):
    return v / np.linalg.norm(v) / np.exp(1.0j * np.angle(v[0]))


def optimize_toffoli(a, b, c):
    program = pq.Program()
    program += pq.gates.H(c)
    program += pq.gates.T(c).dagger()
    program += pq.gates.CNOT(a, c)
    program += pq.gates.T(c)
    program += pq.gates.CNOT(b, c)
    program += pq.gates.T(c).dagger()
    program += pq.gates.CNOT(a, c)
    program += pq.gates.T(c)
    program += pq.gates.H(c)
    return program


def divide_and_conquer(points, qubits, ancilla_qubits, ctrl=None):
    n = int(np.log2(len(points)))
    assert len(points) == 2 ** n

    points = normalize_and_remove_phase(points)
    assert abs(np.linalg.norm(points) - 1.0) < 1e-4
    assert abs(np.angle(points[0])) < 1e-4

    p1 = np.linalg.norm(points[: 2 ** (n - 1)])
    theta = 2 * np.arccos(p1) / np.pi
    phi = np.angle(points[2 ** (n - 1)]) / np.pi

    program = pq.Program()
    if abs(theta) > 1e-4:
        if ctrl is not None:
            program += pq.gates.RY(theta * np.pi, qubits[0]).controlled(ctrl)
        else:
            program += pq.gates.RY(theta * np.pi, qubits[0])
        # if ctrl is not None: program.rz(-.5 * np.pi * theta, ctrl)

    if abs(phi) > 1e-4:
        if ctrl is not None:
            program += pq.gates.RZ(phi * np.pi, qubits[0]).controlled(ctrl)
        else:
            program += pq.gates.RZ(phi * np.pi, qubits[0])
        if ctrl is not None:
            program += pq.gates.RZ(0.5 * phi * np.pi, ctrl)

    if n > 1:
        one_part = points[2 ** (n - 1) :]
        zero_part = points[: 2 ** (n - 1)]

        if np.linalg.norm(one_part) < 1e-4:
            program += divide_and_conquer(zero_part, qubits[1:], ancilla_qubits[1:], ctrl)
        elif np.linalg.norm(zero_part) < 1e-4:
            program += divide_and_conquer(one_part, qubits[1:], ancilla_qubits[1:], ctrl)
        else:
            new_qubits = qubits[1:]
            if ctrl is not None:
                new_ctrl = ancilla_qubits[0]
                new_ancilla_qubits = ancilla_qubits[1:]
                # program.append(cirq.CCX(ctrl,qubits[0],new_ctrl))
                program += optimize_toffoli(ctrl, qubits[0], new_ctrl)
            else:
                new_ctrl = qubits[0]
                new_ancilla_qubits = ancilla_qubits
            program += divide_and_conquer(one_part, new_qubits, new_ancilla_qubits, new_ctrl)
            if ctrl is not None:
                program += pq.gates.CNOT(ctrl, new_ctrl)
            else:
                program += pq.gates.X(new_ctrl)
            program += divide_and_conquer(zero_part, new_qubits, new_ancilla_qubits, new_ctrl)
            if ctrl is not None:
                program += pq.gates.CNOT(ctrl, new_ctrl)
                # program.append(cirq.CCX(ctrl, qubits[0], new_ctrl))

                # This is a symmetric program, so no need to invert
                program += optimize_toffoli(ctrl, qubits[0], new_ctrl)
            else:
                program += pq.gates.X(new_ctrl)
    return program


if __name__ == "__main__":
    from pyquil.quil import Pragma

    n = 2
    state = np.random.rand(2 ** n) + 1.0j * np.random.rand(2 ** n)
    state /= np.linalg.norm(state)
    qubits = list(range(n))
    ancilla_qubits = list(range(n, 2 * n - 2))
    program = pq.Program()
    program += divide_and_conquer(state, qubits, ancilla_qubits)
    psi = pq.api.WavefunctionSimulator().wavefunction(program).amplitudes
    result = psi[: 2 ** n] / np.exp(1.0j * np.angle(psi[0]))

    # Revert the ordering of the qubits
    corrected_result = np.empty(result.shape, dtype=np.complex_)
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
