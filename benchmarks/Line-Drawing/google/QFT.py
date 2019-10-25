import numpy as np
np.set_printoptions(linewidth=200)
import cirq

def QFT(qubits):
    circuit = cirq.Circuit()
    for i,tq in enumerate(qubits):
        circuit.append(cirq.H(tq))
        for j,cq in list(enumerate(qubits))[i+1:]:
            circuit.append(cirq.CZ(cq,tq)**(2**(-(j-i))))
    for i in range(len(qubits)//2):
        circuit.append(cirq.CNOT(qubits[i], qubits[-i-1]))
        circuit.append(cirq.CNOT(qubits[-i-1], qubits[i]))
        circuit.append(cirq.CNOT(qubits[i], qubits[-i-1]))
    return circuit

if __name__ == '__main__':
    qubits = [cirq.GridQubit(0,i) for i in range(3)]
    circuit = QFT(qubits)
    print(circuit)
    print(np.round(circuit.to_unitary_matrix(),3))
