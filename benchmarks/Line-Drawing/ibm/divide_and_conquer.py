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
                circuit,
                new_qubits,
                new_ancilla_qubits,
                points[2 ** (n - 1) :],
                new_ctrl,
            )
            if ctrl is not None:
                circuit.cx(ctrl, new_ctrl)
            else:
                circuit.x(new_ctrl)
            divide_and_conquer(
                circuit,
                new_qubits,
                new_ancilla_qubits,
                points[: 2 ** (n - 1)],
                new_ctrl,
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

    num_qubits = 4
    N = 2 ** num_qubits
    # points = np.exp(2.j * np.pi * np.arange(N) / N) / np.sqrt(N)
    points = normalize_and_remove_phase(np.random.rand(N) + 1.0j * np.random.rand(N))
    # points = np.array([0,0,0,0.70710678+0.70710678j])
    # points = np.array([0.45621777+0.j, 0.17273829+0.12513561j, 0.59497154+0.22042816j, 0.57531933+0.11311881j])
    np.set_printoptions(linewidth=200)
    print("State to prepare:", points)

    # Set up circuit
    n = int(np.log2(len(points)))
    qubits = list(range(n))
    ancilla_qubits = list(range(n, 2 * n - 2))
    circuit = QuantumCircuit(len(qubits) + len(ancilla_qubits))
    divide_and_conquer(circuit, qubits, ancilla_qubits, points)
    print(circuit)

    # Simulate
    backend = Aer.get_backend("statevector_simulator")
    # for i in range(len(circuit.data)+1):
    #     tmp_circuit = circuit.copy()
    #     tmp_circuit.data = tmp_circuit.data[:i]
    #     psi = execute(tmp_circuit, backend).result().get_statevector()
    #     result = psi[:2**n] / np.exp(1.j * np.angle(psi[0]))
    #     corrected_result = np.empty(result.shape, dtype = np.complex_)
    #     for i,r in enumerate(result):
    #         corrected_result[int(''.join(reversed(f"{i:0{n}b}")),2)] = r
    #     print(np.round(corrected_result,3))
    psi = execute(circuit, backend).result().get_statevector()
    result = psi[: 2 ** n] / np.exp(1.0j * np.angle(psi[0]))
    corrected_result = np.empty(result.shape, dtype=np.complex_)
    for i, r in enumerate(result):
        corrected_result[int("".join(reversed(f"{i:0{n}b}")), 2)] = r
    print(corrected_result)
    print(np.abs(corrected_result) - np.abs(points))
    print(np.angle(corrected_result) - np.angle(points))

    # Check resulting state
    print("Norm of the resulting vector:", np.linalg.norm(corrected_result))
    print("Maximum absolute error:", np.max(np.abs(corrected_result - points)))
    print(
        "Inner product error:",
        abs(abs(np.sum(np.conj(corrected_result) * points)) - 1.0),
    )
