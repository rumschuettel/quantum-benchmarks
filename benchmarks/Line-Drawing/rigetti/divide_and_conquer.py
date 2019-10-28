import numpy as np
import pyquil as pq

def normalize_and_remove_phase(v):
    return v / np.linalg.norm(v) / np.exp(1.j * np.angle(v[0]))

def optimize_toffoli(a,b,c):
    program = pq.Program()
    program += pq.gates.H(c)
    program += pq.gates.T(c).dagger()
    program += pq.gates.CNOT(a,c)
    program += pq.gates.T(c)
    program += pq.gates.CNOT(b,c)
    program += pq.gates.T(c).dagger()
    program += pq.gates.CNOT(a,c)
    program += pq.gates.T(c)
    program += pq.gates.H(c)
    return program

def divide_and_conquer(points, qubits, ancilla_qubits, ctrl = None):
    n = int(np.log2(len(points)))
    assert len(points) == 2**n

    points = normalize_and_remove_phase(points)
    assert abs(np.linalg.norm(points) - 1.) < 1e-4
    assert abs(np.angle(points[0])) < 1e-4

    p1 = np.linalg.norm(points[:2**(n-1)])
    theta = 2 * np.arccos(p1) / np.pi
    phi = np.angle(points[2**(n-1)]) / np.pi

    program = pq.Program()
    if abs(theta) > 1e-4:
        if ctrl is not None: program += pq.gates.RY(theta * np.pi, qubits[0]).controlled(ctrl)
        else: program += pq.gates.RY(theta * np.pi, qubits[0])
        # if ctrl is not None: program.rz(-.5 * np.pi * theta, ctrl)

    if abs(phi) > 1e-4:
        if ctrl is not None: program += pq.gates.RZ(phi * np.pi, qubits[0]).controlled(ctrl)
        else: program += pq.gates.RZ(phi * np.pi, qubits[0])
        if ctrl is not None: program += pq.gates.RZ(.5 * phi * np.pi, ctrl)

    if n > 1:
        one_part = points[2**(n-1):]
        zero_part = points[:2**(n-1)]

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
            if ctrl is not None: program += pq.gates.CNOT(ctrl, new_ctrl)
            else: program += pq.gates.X(new_ctrl)
            program += divide_and_conquer(zero_part, new_qubits, new_ancilla_qubits, new_ctrl)
            if ctrl is not None:
                program += pq.gates.CNOT(ctrl, new_ctrl)
                # program.append(cirq.CCX(ctrl, qubits[0], new_ctrl))

                # This is a symmetric program, so no need to invert
                program += optimize_toffoli(ctrl, qubits[0], new_ctrl)
            else: program += pq.gates.X(new_ctrl)
    return program

if __name__ == '__main__':
    from pyquil.quil import Pragma
    num_qubits = 4
    N = 2**num_qubits
    # points = np.exp(2.j * np.pi * np.arange(N) / N) / np.sqrt(N)
    points = normalize_and_remove_phase(np.random.rand(N) + 1.j * np.random.rand(N))
    # points = np.array([0,0,0,0.70710678+0.70710678j])
    # points = np.array([0.45621777+0.j, 0.17273829+0.12513561j, 0.59497154+0.22042816j, 0.57531933+0.11311881j])
    np.set_printoptions(linewidth=200)
    print("State to prepare:", points)

    # Set up program
    n = int(np.log2(len(points)))
    qubits = list(range(n))
    ancilla_qubits = list(range(n,2*n-2))
    program = pq.Program()
    program += Pragma('INITIAL_REWIRING', ['"GREEDY"'])
    program += divide_and_conquer(points, qubits, ancilla_qubits)
    print(program)

    # Simulate
    # for i in range(len(program.data)+1):
    #     tmp_program = program.copy()
    #     tmp_program.data = tmp_program.data[:i]
    #     psi = execute(tmp_program, backend).result().get_statevector()
    #     result = psi[:2**n] / np.exp(1.j * np.angle(psi[0]))
    #     corrected_result = np.empty(result.shape, dtype = np.complex_)
    #     for i,r in enumerate(result):
    #         corrected_result[int(''.join(reversed(f"{i:0{n}b}")),2)] = r
    #     print(np.round(corrected_result,3))
    psi = pq.api.WavefunctionSimulator().wavefunction(program).amplitudes
    result = psi[:2**n] / np.exp(1.j * np.angle(psi[0]))
    corrected_result = np.empty(result.shape, dtype = np.complex_)
    for i,r in enumerate(result):
        corrected_result[int(''.join(reversed(f"{i:0{n}b}")),2)] = r
    print(corrected_result)
    print(np.abs(corrected_result) - np.abs(points))
    print(np.angle(corrected_result) - np.angle(points))

    # Check resulting state
    print("Norm of the resulting vector:", np.linalg.norm(corrected_result))
    print("Maximum absolute error:", np.max(np.abs(corrected_result - points)))
    print("Inner product error:", abs(abs(np.sum(np.conj(corrected_result) * points)) - 1.))
