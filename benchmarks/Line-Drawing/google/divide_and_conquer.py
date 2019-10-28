import numpy as np
import cirq


def normalize_and_remove_phase(v):
    return v / np.linalg.norm(v) / np.exp(1.0j * np.angle(v[0]))
    # return v / np.linalg.norm(v) / np.exp(1.j * np.mean(np.angle(v)))


def optimize_toffoli(a, b, c):
    circuit = cirq.Circuit()
    circuit.append(cirq.H(c))
    circuit.append(cirq.inverse(cirq.T(c)))
    circuit.append(cirq.CNOT(a, c))
    circuit.append(cirq.T(c))
    circuit.append(cirq.CNOT(b, c))
    circuit.append(cirq.inverse(cirq.T(c)))
    circuit.append(cirq.CNOT(a, c))
    circuit.append(cirq.T(c))
    circuit.append(cirq.H(c))
    return circuit


def divide_and_conquer(points, qubits, ancilla_qubits, ctrl=None):
    # This function returns a circuit that acts on the qubits as provided in "qubits",
    # and maps the all zeros state to the state where the amplitudes are given by the variable "points".
    # If "ctrl" is a qubit instead of None, then the circuit is controlled on this qubit being in the $|1>$ state.
    n = int(np.log2(len(points)))
    assert len(points) == 2 ** n

    points = normalize_and_remove_phase(points)
    assert abs(np.linalg.norm(points) - 1.0) < 1e-4
    assert abs(np.angle(points[0])) < 1e-4
    # assert abs(np.mean(np.angle(points))) < 1e-4

    p1 = np.linalg.norm(points[: 2 ** (n - 1)])
    theta = 2 * np.arccos(p1) / np.pi
    phi = np.angle(points[2 ** (n - 1)]) / np.pi
    # phi = np.mean(np.angle(points[2**(n-1):]))

    circuit = cirq.Circuit()

    if abs(theta) > 1e-4:
        opY = cirq.Y(qubits[0]) ** theta
        if ctrl is not None:
            opY = opY.controlled_by(ctrl)
        circuit.append(opY)

        if ctrl is not None:
            circuit.append(cirq.Z(ctrl) ** (-theta / 2))

    if abs(phi) > 1e-4:
        opZ = cirq.Z(qubits[0]) ** phi
        if ctrl is not None:
            opZ = opZ.controlled_by(ctrl)
        circuit.append(opZ)

    if n > 1:
        one_part = points[2 ** (n - 1) :]
        zero_part = points[: 2 ** (n - 1)]

        if np.linalg.norm(one_part) < 1e-4:
            circuit.append(
                divide_and_conquer(zero_part, qubits[1:], ancilla_qubits[1:], ctrl)
            )
        elif np.linalg.norm(zero_part) < 1e-4:
            circuit.append(
                divide_and_conquer(one_part, qubits[1:], ancilla_qubits[1:], ctrl)
            )
        else:
            new_qubits = qubits[1:]
            if ctrl is not None:
                new_ctrl = ancilla_qubits[0]
                new_ancilla_qubits = ancilla_qubits[1:]
                # circuit.append(cirq.CCX(ctrl,qubits[0],new_ctrl))
                circuit.append(optimize_toffoli(ctrl, qubits[0], new_ctrl))
            else:
                new_ctrl = qubits[0]
                new_ancilla_qubits = ancilla_qubits
            circuit.append(
                divide_and_conquer(one_part, new_qubits, new_ancilla_qubits, new_ctrl)
            )
            if ctrl is not None:
                circuit.append(cirq.CNOT(ctrl, new_ctrl))
            else:
                circuit.append(cirq.X(new_ctrl))
            circuit.append(
                divide_and_conquer(zero_part, new_qubits, new_ancilla_qubits, new_ctrl)
            )
            if ctrl is not None:
                circuit.append(cirq.CNOT(ctrl, new_ctrl))
                # circuit.append(cirq.CCX(ctrl, qubits[0], new_ctrl))
                circuit.append(
                    cirq.inverse(optimize_toffoli(ctrl, qubits[0], new_ctrl))
                )
            else:
                circuit.append(cirq.X(new_ctrl))
    return circuit


if __name__ == "__main__":
    num_qubits = 2
    N = 2 ** num_qubits
    # points = np.exp(2.j * np.pi * np.arange(N) / N) / np.sqrt(N)
    # points = normalize_and_remove_phase(np.random.rand(N) + 1.j * np.random.rand(N))
    # points = np.array([0,0,0,0.70710678+0.70710678j])
    points = np.array(
        [
            0.45621777 + 0.0j,
            0.17273829 + 0.12513561j,
            0.59497154 + 0.22042816j,
            0.57531933 + 0.11311881j,
        ]
    )
    np.set_printoptions(linewidth=200)
    print("State to prepare:", points)

    # Set up circuit
    n = int(np.log2(len(points)))
    qubits = [cirq.GridQubit(0, i) for i in range(n)]
    ancilla_qubits = [cirq.GridQubit(1, i) for i in range(n - 2)]
    circuit = divide_and_conquer(points, qubits, ancilla_qubits)
    print(circuit)

    # Simulate
    all_qubits = qubits + ancilla_qubits
    # for i in range(len(circuit)+1):
    #     tmp_circuit = cirq.Circuit()
    #     tmp_circuit._moments = circuit._moments[:i]
    #     psi = cirq.Simulator().simulate(tmp_circuit, qubit_order = all_qubits).final_state
    #     result = psi[::2**len(ancilla_qubits)] / np.exp(1.j * np.angle(psi[0]))
    #     print(np.round(result,3))

    psi = cirq.Simulator().simulate(circuit, qubit_order=all_qubits).final_state
    result = psi[:: 2 ** len(ancilla_qubits)] / np.exp(1.0j * np.angle(psi[0]))
    print(result)

    # Check resulting state
    print("Norm of the resulting vector:", np.linalg.norm(result))
    print("Maximum absolute error:", np.max(np.abs(result - points)))
    print("Inner product error:", abs(abs(np.sum(np.conj(result) * points)) - 1.0))
