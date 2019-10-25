import numpy as np
import cirq

def normalize_and_remove_phase(v):
    return v / np.linalg.norm(v) / np.exp(1.j * np.angle(v[0]))

def optimize_toffoli(a,b,c):
    circuit = cirq.Circuit()
    circuit.append(cirq.H(c))
    circuit.append(cirq.inverse(cirq.T(c)))
    circuit.append(cirq.CNOT(a,c))
    circuit.append(cirq.T(c))
    circuit.append(cirq.CNOT(b,c))
    circuit.append(cirq.inverse(cirq.T(c)))
    circuit.append(cirq.CNOT(a,c))
    circuit.append(cirq.T(c))
    circuit.append(cirq.H(c))
    return circuit

def divide_and_conquer(points, qubits, ancilla_qubits, ctrl = None):
    n = int(np.log2(len(points)))
    assert len(points) == 2**n

    points = normalize_and_remove_phase(points)
    assert abs(np.linalg.norm(points) - 1.) < 1e-4
    assert abs(np.angle(points[0])) < 1e-4

    p1 = np.linalg.norm(points[:2**(n-1)])
    theta = 2 * np.arccos(p1) / np.pi
    phi = np.angle(points[2**(n-1)]) / np.pi

    circuit = cirq.Circuit()

    opY = cirq.Y(qubits[0])**theta
    if ctrl is not None: opY = opY.controlled_by(ctrl)
    circuit.append(opY)

    opZ = cirq.Z(qubits[0])**phi
    if ctrl is not None: opZ = opZ.controlled_by(ctrl)
    circuit.append(opZ)

    if ctrl is not None: circuit.append(cirq.Z(ctrl)**(-theta/2))

    if n > 1:
        new_qubits = qubits[1:]
        if ctrl is not None:
            new_ctrl = ancilla_qubits[0]
            new_ancilla_qubits = ancilla_qubits[1:]
            # circuit.append(cirq.CCX(ctrl,qubits[0],new_ctrl))
            circuit.append(optimize_toffoli(ctrl,qubits[0],new_ctrl))
        else:
            new_ctrl = qubits[0]
            new_ancilla_qubits = ancilla_qubits
        circuit.append(divide_and_conquer(points[2**(n-1):], new_qubits, new_ancilla_qubits, new_ctrl))
        if ctrl is not None: circuit.append(cirq.CNOT(ctrl, new_ctrl))
        else: circuit.append(cirq.X(new_ctrl))
        circuit.append(divide_and_conquer(points[:2**(n-1)], new_qubits, new_ancilla_qubits, new_ctrl))
        if ctrl is not None:
            circuit.append(cirq.CNOT(ctrl, new_ctrl))
            # circuit.append(cirq.CCX(ctrl, qubits[0], new_ctrl))
            circuit.append(cirq.inverse(optimize_toffoli(ctrl,qubits[0],new_ctrl)))
        else: circuit.append(cirq.X(new_ctrl))
    return circuit

if __name__ == '__main__':
    num_qubits = 3
    N = 2**num_qubits
    points = np.exp(2.j * np.pi * np.arange(N) / N) / np.sqrt(N)

    # Set up circuit
    n = int(np.log2(len(points)))
    qubits = [cirq.GridQubit(0,i) for i in range(n)]
    ancilla_qubits = [cirq.GridQubit(1,i) for i in range(n-2)]
    circuit = divide_and_conquer(points, qubits, ancilla_qubits)
    print(circuit)

    # Simulate
    all_qubits = qubits + ancilla_qubits
    psi = cirq.Simulator().simulate(circuit, qubit_order = all_qubits).final_state
    result = psi[::2**len(ancilla_qubits)] / np.exp(1.j * np.angle(psi[0]))

    # Check resulting state
    print("Norm of the resulting vector:", np.linalg.norm(result))
    print("Maximum absolute error:", np.max(np.abs(result - points)))
