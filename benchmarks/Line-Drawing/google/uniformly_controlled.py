import numpy as np
import cirq

H = np.array([[1,1],[1,-1]]) / np.sqrt(2)
S = np.array([[1,0],[0,1.j]])
X = np.array([[0,1],[1,0]])
CNOT = np.zeros((4,4), dtype = np.complex_)
CNOT[:2,:2] = np.eye(2)
CNOT[2:,2:] = X

def decompose_singly_controlled_unitaries(A,B):
    # The discriminant matrix
    X = A @ np.conj(B.T)
    if abs(X[0,0]) < 1e-8 and abs(X[1,1]) < 1e-8:
        theta = np.angle(X[1,0]) + np.angle(X[0,1]) - np.pi
    else:
        theta = np.angle(X[0,0]) + np.angle(X[1,1])

    # Calculate diagonal entries of R matrix
    if abs(X[0,0]) < 1e-8 and abs(X[1,1]) < 1e-8:
        phi = 0
    else:
        phi = np.angle(X[0,0] / np.exp(.5j * theta))
    R = np.diag([np.exp(-.25j * theta + .5j * (.5 * np.pi - phi)), np.exp(-.25j * theta - .5j * (.5 * np.pi - phi))])

    # Calculate U and V
    D2,U = np.linalg.eig(R @ X @ R)
    if abs(D2[0] + 1.j) < 1e-4:
        D2[1],D2[0] = D2[0],D2[1]
        U[0,0],U[1,0],U[0,1],U[1,1] = U[0,1],U[1,1],U[0,0],U[1,0]
    D = np.diag(np.sqrt(D2))
    V = np.conj(D.T) @ np.conj(U.T) @ R @ A

    # The operation we want to implement
    op = np.zeros((4,4), dtype = np.complex_)
    op[:2,:2] = A
    op[2:,2:] = B

    # Decompose D and absorb into U and V
    V = H @ V
    U = U @ np.conj(S.T) @ H

    # Construct full diagonal matrix
    fullR = np.zeros((4,4), dtype = np.complex_)
    fullR[:2,:2] = np.conj(R.T) * np.exp(1.j * np.pi/4)
    fullR[2:,2:] = R * np.exp(1.j * np.pi/4)
    fullR = fullR @ np.kron(np.conj(S.T), np.eye(2))

    # Check if operation is equal
    O = fullR @ np.kron(np.eye(2), U) @ CNOT @ np.kron(np.eye(2), V)
    print("Single control error:", np.max(np.abs(O - op)))

    # Return the operations U, V and the full diagonal matrix
    return U,V,np.diag(fullR)

def reconstruct_operation(Gs, Rs):
    n = int(np.log2(len(Gs)))
    assert len(Gs) == 2**n

    full_operation = np.eye(2**(n+1), dtype = np.complex_)
    for i,G in enumerate(Gs):
        # Apply the gate
        new_operation = np.zeros((2**(n+1), 2**(n+1)), dtype = np.complex_)
        for j in range(2**n):
            new_operation[2*j:2*j+2,2*j:2*j+2] = G
        full_operation = new_operation @ full_operation

        # If this was the last gate, stop
        if i == 2**n - 1: break

        # Apply the CNOT gate
        i += 1
        ctr = 0
        while i%2 == 0 and i > 0:
            ctr += 1
            i //= 2
        CNOT_operation = np.zeros((2**(n+1), 2**(n+1)), dtype = np.complex_)
        for i in range(2**(n+1)):
            if (i // 2**(ctr+1)) % 2 == 1:
                if i%2 == 1:
                    CNOT_operation[i,i-1] = 1
                else:
                    CNOT_operation[i,i+1] = 1
            else:
                CNOT_operation[i,i] = 1
        full_operation = CNOT_operation @ full_operation

    # Apply the final diagonal gate
    full_operation = np.diag(Rs) @ full_operation

    # Return the operation
    return full_operation

def decompose_uniformly_controlled_unitaries(unitaries):
    n = int(np.log2(len(unitaries)))
    assert len(unitaries) == 2**n

    # If there is no control qubit, just return the unitary and a bogus zero phase
    if n == 0:
        return unitaries, np.array([1,1])

    # If there is just one control qubit, return the single decomposition
    if n == 1:
        A,B = unitaries
        U,V,R = decompose_singly_controlled_unitaries(A,B)
        return [V,U],R

    # Decompose the given uniformly controlled operation
    Us,Vs,Rs = [],[],np.zeros(2**(n+1), dtype = np.complex_)
    for i,(A,B) in enumerate(zip(unitaries[:2**(n-1)], unitaries[2**(n-1):])):
        U,V,R = decompose_singly_controlled_unitaries(A,B)
        Us.append(U)
        Vs.append(V)
        Rs[2*i],Rs[2*i+1],Rs[2**n+2*i],Rs[2**n+2*i+1] = R

    # Check if the decomposition worked
    fullU = np.zeros((2**n, 2**n), dtype = np.complex_)
    fullV = np.zeros((2**n, 2**n), dtype = np.complex_)
    fullCNOT = np.zeros((2**(n+1), 2**(n+1)), dtype = np.complex_)
    for i,(U,V) in enumerate(zip(Us,Vs)):
        fullU[2*i:2*i+2,2*i:2*i+2] = U
        fullV[2*i:2*i+2,2*i:2*i+2] = V
        fullCNOT[2*i:2*i+2,2*i:2*i+2] = np.eye(2)
        fullCNOT[2**n+2*i:2**n+2*i+2,2**n+2*i:2**n+2*i+2] = X
    constructed_unitary = np.diag(Rs) @ np.kron(np.eye(2), fullU) @ fullCNOT @ np.kron(np.eye(2), fullV)

    full_unitary = np.zeros((2**(n+1), 2**(n+1)), dtype = np.complex_)
    for i,unitary in enumerate(unitaries):
        full_unitary[2*i:2*i+2,2*i:2*i+2] = unitary

    # Check if decomposition worked
    print("Full construction error:", np.max(np.abs(full_unitary - constructed_unitary)))

    # Implement the Vs, minus the Hadamards at the end
    Vs = [H @ V for V in Vs]
    VGs,VR = decompose_uniformly_controlled_unitaries(Vs)

    # Check if decomposition worked
    new_fullV = reconstruct_operation(VGs, VR)
    new_fullV = np.kron(np.eye(2**(n-1)), H) @ new_fullV
    print("V error:", np.max(np.abs(fullV - new_fullV)))

    # Merge the last H gate into the V gate array
    VGs[-1] = H @ VGs[-1]

    # Remove the Hadamard gate from the uniformly controlled Us
    Us = [U @ H for U in Us]

    # Correct for the phases from the V part
    for i,U in enumerate(Us):
        Us[i] = U @ np.diag([VR[2*i],VR[2*i+1]])

    # Implement the Us, minus the Hadamards at the start
    UGs,UR = decompose_uniformly_controlled_unitaries(Us)

    # Merge the starting H into the first gate
    UGs[0] = UGs[0] @ H

    # Correct the phases in the final diagonal unitary
    for i,r in enumerate(UR):
        Rs[i] *= r
        Rs[i+2**n] *= r

    # Merge the gates into one list
    Gs = VGs + UGs

    # Check if the operations check out
    full_operation = reconstruct_operation(Gs, Rs)

    # Check the results
    print("Full operation error:", np.max(np.abs(full_operation - full_unitary)))

    # Return the gates and the diagonal unitary
    return Gs, Rs

def decompose_single_qubit_unitary(U):
    if abs(U[1,0]) < 1e-8 and abs(U[0,1]) < 1e-8:
        phi = np.angle(U[0,0])
        U = U / np.exp(1.j * phi)
        c = 0
        b = 0
        a = np.angle(U[1,1]) / np.pi
    elif abs(U[0,0]) < 1e-8 and abs(U[1,1]) < 1e-8:
        phi = np.angle(U[1,0])
        U = U / np.exp(1.j * phi)
        # print(U)
        c = 0
        b = 1
        a = np.angle(-U[0,1]) / np.pi
    else:
        phi = np.angle(U[0,0])
        U = U / np.exp(1.j * phi)
        c = np.angle(U[1,0]) / np.pi
        b = 2 * np.arctan2(abs(U[1,0]), abs(U[0,0])) / np.pi
        a = np.angle(-U[0,1]) / np.pi

    Utilde = np.diag([1, np.exp(1.j * np.pi * c)]) \
        @ np.array([[np.cos(.5*np.pi*b), -np.sin(.5*np.pi*b)], [np.sin(.5*np.pi*b), np.cos(.5*np.pi*b)]]) \
        @ np.diag([1, np.exp(1.j * np.pi * a)])
    print("Single qubit gate error:", np.max(np.abs(U - Utilde)))

    return phi,a,b,c

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
