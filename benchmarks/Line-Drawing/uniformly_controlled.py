import numpy as np

H = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
S = np.array([[1, 0], [0, 1.0j]])
X = np.array([[0, 1], [1, 0]])
CNOT = np.zeros((4, 4), dtype=np.complex_)
CNOT[:2, :2] = np.eye(2)
CNOT[2:, 2:] = X


def decompose_singly_controlled_unitaries(A, B):
    # The discriminant matrix
    X = A @ np.conj(B.T)
    if abs(X[0, 0]) < 1e-8 and abs(X[1, 1]) < 1e-8:
        theta = np.angle(X[1, 0]) + np.angle(X[0, 1]) - np.pi
    else:
        theta = np.angle(X[0, 0]) + np.angle(X[1, 1])

    # Calculate diagonal entries of R matrix
    if abs(X[0, 0]) < 1e-8 and abs(X[1, 1]) < 1e-8:
        phi = 0
    else:
        phi = np.angle(X[0, 0] / np.exp(0.5j * theta))
    R = np.diag(
        [
            np.exp(-0.25j * theta + 0.5j * (0.5 * np.pi - phi)),
            np.exp(-0.25j * theta - 0.5j * (0.5 * np.pi - phi)),
        ]
    )

    # Calculate U and V
    D2, U = np.linalg.eig(R @ X @ R)
    if abs(D2[0] + 1.0j) < 1e-4:
        D2[1], D2[0] = D2[0], D2[1]
        U[0, 0], U[1, 0], U[0, 1], U[1, 1] = U[0, 1], U[1, 1], U[0, 0], U[1, 0]
    D = np.diag(np.sqrt(D2))
    V = np.conj(D.T) @ np.conj(U.T) @ R @ A

    # The operation we want to implement
    op = np.zeros((4, 4), dtype=np.complex_)
    op[:2, :2] = A
    op[2:, 2:] = B

    # Decompose D and absorb into U and V
    V = H @ V
    U = U @ np.conj(S.T) @ H

    # Construct full diagonal matrix
    fullR = np.zeros((4, 4), dtype=np.complex_)
    fullR[:2, :2] = np.conj(R.T) * np.exp(1.0j * np.pi / 4)
    fullR[2:, 2:] = R * np.exp(1.0j * np.pi / 4)
    fullR = fullR @ np.kron(np.conj(S.T), np.eye(2))

    # Check if operation is equal
    O = fullR @ np.kron(np.eye(2), U) @ CNOT @ np.kron(np.eye(2), V)
    single_control_error = np.max(np.abs(O - op))
    assert single_control_error < 1e-8, f"Single control error: {single_control_error}"

    # Return the operations U, V and the full diagonal matrix
    return U, V, np.diag(fullR)


def reconstruct_operation(Gs, Rs):
    n = int(np.log2(len(Gs)))
    assert len(Gs) == 2 ** n

    full_operation = np.eye(2 ** (n + 1), dtype=np.complex_)
    for i, G in enumerate(Gs):
        # Apply the gate
        new_operation = np.zeros((2 ** (n + 1), 2 ** (n + 1)), dtype=np.complex_)
        for j in range(2 ** n):
            new_operation[2 * j : 2 * j + 2, 2 * j : 2 * j + 2] = G
        full_operation = new_operation @ full_operation

        # If this was the last gate, stop
        if i == 2 ** n - 1:
            break

        # Apply the CNOT gate
        i += 1
        ctr = 0
        while i % 2 == 0 and i > 0:
            ctr += 1
            i //= 2
        CNOT_operation = np.zeros((2 ** (n + 1), 2 ** (n + 1)), dtype=np.complex_)
        for i in range(2 ** (n + 1)):
            if (i // 2 ** (ctr + 1)) % 2 == 1:
                if i % 2 == 1:
                    CNOT_operation[i, i - 1] = 1
                else:
                    CNOT_operation[i, i + 1] = 1
            else:
                CNOT_operation[i, i] = 1
        full_operation = CNOT_operation @ full_operation

    # Apply the final diagonal gate
    full_operation = np.diag(Rs) @ full_operation

    # Return the operation
    return full_operation


def decompose_uniformly_controlled_unitaries(unitaries):
    n = int(np.log2(len(unitaries)))
    assert len(unitaries) == 2 ** n

    # If there is no control qubit, just return the unitary and a bogus zero phase
    if n == 0:
        return unitaries, np.array([1, 1])

    # If there is just one control qubit, return the single decomposition
    if n == 1:
        A, B = unitaries
        U, V, R = decompose_singly_controlled_unitaries(A, B)
        return [V, U], R

    # Decompose the given uniformly controlled operation
    Us, Vs, Rs = [], [], np.zeros(2 ** (n + 1), dtype=np.complex_)
    for i, (A, B) in enumerate(
        zip(unitaries[: 2 ** (n - 1)], unitaries[2 ** (n - 1) :])
    ):
        U, V, R = decompose_singly_controlled_unitaries(A, B)
        Us.append(U)
        Vs.append(V)
        Rs[2 * i], Rs[2 * i + 1], Rs[2 ** n + 2 * i], Rs[2 ** n + 2 * i + 1] = R

    # Check if the decomposition worked
    fullU = np.zeros((2 ** n, 2 ** n), dtype=np.complex_)
    fullV = np.zeros((2 ** n, 2 ** n), dtype=np.complex_)
    fullCNOT = np.zeros((2 ** (n + 1), 2 ** (n + 1)), dtype=np.complex_)
    for i, (U, V) in enumerate(zip(Us, Vs)):
        fullU[2 * i : 2 * i + 2, 2 * i : 2 * i + 2] = U
        fullV[2 * i : 2 * i + 2, 2 * i : 2 * i + 2] = V
        fullCNOT[2 * i : 2 * i + 2, 2 * i : 2 * i + 2] = np.eye(2)
        fullCNOT[
            2 ** n + 2 * i : 2 ** n + 2 * i + 2, 2 ** n + 2 * i : 2 ** n + 2 * i + 2
        ] = X
    constructed_unitary = (
        np.diag(Rs) @ np.kron(np.eye(2), fullU) @ fullCNOT @ np.kron(np.eye(2), fullV)
    )

    full_unitary = np.zeros((2 ** (n + 1), 2 ** (n + 1)), dtype=np.complex_)
    for i, unitary in enumerate(unitaries):
        full_unitary[2 * i : 2 * i + 2, 2 * i : 2 * i + 2] = unitary

    # Check if decomposition worked
    full_construction_error = np.max(np.abs(full_unitary - constructed_unitary))
    assert (
        full_construction_error < 1e-8
    ), f"Full construction error: {full_construction_error}"

    # Implement the Vs, minus the Hadamards at the end
    Vs = [H @ V for V in Vs]
    VGs, VR = decompose_uniformly_controlled_unitaries(Vs)

    # Check if decomposition worked
    new_fullV = reconstruct_operation(VGs, VR)
    new_fullV = np.kron(np.eye(2 ** (n - 1)), H) @ new_fullV
    V_error = np.max(np.abs(fullV - new_fullV))
    assert V_error < 1e-8, f"V error: {V_error}"

    # Merge the last H gate into the V gate array
    VGs[-1] = H @ VGs[-1]

    # Remove the Hadamard gate from the uniformly controlled Us
    Us = [U @ H for U in Us]

    # Correct for the phases from the V part
    for i, U in enumerate(Us):
        Us[i] = U @ np.diag([VR[2 * i], VR[2 * i + 1]])

    # Implement the Us, minus the Hadamards at the start
    UGs, UR = decompose_uniformly_controlled_unitaries(Us)

    # Merge the starting H into the first gate
    UGs[0] = UGs[0] @ H

    # Correct the phases in the final diagonal unitary
    for i, r in enumerate(UR):
        Rs[i] *= r
        Rs[i + 2 ** n] *= r

    # Merge the gates into one list
    Gs = VGs + UGs

    # Check if the operations check out
    full_operation = reconstruct_operation(Gs, Rs)

    # Check the results
    full_operation_error = np.max(np.abs(full_operation - full_unitary))
    assert full_operation_error < 1e-8, f"Full operation error: {full_operation_error}"

    # Return the gates and the diagonal unitary
    return Gs, Rs


def decompose_single_qubit_unitary(U):
    if abs(U[1, 0]) < 1e-8 and abs(U[0, 1]) < 1e-8:
        phi = np.angle(U[0, 0])
        U = U / np.exp(1.0j * phi)
        c = 0
        b = 0
        a = np.angle(U[1, 1]) / np.pi
    elif abs(U[0, 0]) < 1e-8 and abs(U[1, 1]) < 1e-8:
        phi = np.angle(U[1, 0])
        U = U / np.exp(1.0j * phi)
        # print(U)
        c = 0
        b = 1
        a = np.angle(-U[0, 1]) / np.pi
    else:
        phi = np.angle(U[0, 0])
        U = U / np.exp(1.0j * phi)
        c = np.angle(U[1, 0]) / np.pi
        b = 2 * np.arctan2(abs(U[1, 0]), abs(U[0, 0])) / np.pi
        a = np.angle(-U[0, 1]) / np.pi

    Utilde = (
        np.diag([1, np.exp(1.0j * np.pi * c)])
        @ np.array(
            [
                [np.cos(0.5 * np.pi * b), -np.sin(0.5 * np.pi * b)],
                [np.sin(0.5 * np.pi * b), np.cos(0.5 * np.pi * b)],
            ]
        )
        @ np.diag([1, np.exp(1.0j * np.pi * a)])
    )
    single_qubit_error = np.max(np.abs(U - Utilde))
    assert single_qubit_error < 1e-8, f"Single qubit gate error: {single_qubit_error}"

    return phi, a, b, c
