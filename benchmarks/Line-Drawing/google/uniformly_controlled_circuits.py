import numpy as np
import cirq

from ..uniformly_controlled import decompose_single_qubit_unitary, decompose_uniformly_controlled_unitaries

def generate_single_qubit_circuit(U, qubit):
    _,a,b,c = decompose_single_qubit_unitary(U)
    circuit = cirq.Circuit()
    circuit.append(cirq.Z(qubit)**a)
    circuit.append(cirq.Y(qubit)**b)
    circuit.append(cirq.Z(qubit)**c)
    return circuit

def fill_uniformly_controlled_circuit(Gs, cqs, tq):
    n = len(cqs)
    circuit = cirq.Circuit()
    if n == 0:
        circuit.append(generate_single_qubit_circuit(Gs[0], tq))
    else:
        circuit.append(fill_uniformly_controlled_circuit(Gs[:2**(n-1)], cqs[1:], tq))
        circuit.append(cirq.CNOT(cqs[0], tq))
        circuit.append(fill_uniformly_controlled_circuit(Gs[2**(n-1):], cqs[1:], tq))
    return circuit

def generate_uniformly_controlled_circuit(unitaries, cqs, tq):
    assert len(unitaries) == 2**len(cqs)
    n = len(cqs)

    # Obtain the single qubit unitaries
    Gs,Rs = decompose_uniformly_controlled_unitaries(unitaries)
    assert len(Gs) == 2**n

    # Return the result
    return fill_uniformly_controlled_circuit(Gs, cqs, tq), Rs

if __name__ == '__main__':
    from scipy.stats import unitary_group
    n = 2
    unitaries = [unitary_group.rvs(2) for _ in range(2**n)]
    qubits = [cirq.GridQubit(0,i) for i in range(n+1)]
    circuit, R = generate_uniformly_controlled_circuit(unitaries, qubits[:n], qubits[-1])
    print("Circuit:")
    print(circuit)
    print("Phases:")
    print(R)

    M = np.diag(R) @ circuit.to_unitary_matrix()
    print("Implemented unitary:")
    print(np.round(M / np.exp(1.j * np.angle(M[0,0])),3))

    full_unitary = np.zeros((2**(n+1), 2**(n+1)), dtype = np.complex_)
    for i,unitary in enumerate(unitaries):
        full_unitary[2*i:2*i+2,2*i:2*i+2] = unitary
    print("Full unitary:")
    print(np.round(full_unitary / np.exp(1.j * np.angle(full_unitary[0,0])), 3))
    print("Error:", np.max(np.abs(full_unitary / np.exp(1.j * np.angle(full_unitary[0,0])) - M / np.exp(1.j * np.angle(M[0,0])))))
