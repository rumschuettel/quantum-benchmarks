import numpy as np


def normalize_and_remove_phase(v):
    return v / np.linalg.norm(v) / np.exp(1.0j * np.angle(v[0]))


def Shende_Bullock_Markov(circuit, qubits, state, GRAY_CODE=True, REVERSE_ZS=True):
    state = np.array(state, dtype = np.complex64)
    assert len(state) == 2 ** len(qubits)
    assert abs(np.linalg.norm(state) - 1.0) < 1e-8

    n = len(qubits)
    for i in range(n):
        states = [
            normalize_and_remove_phase(
                np.array(
                    [
                        np.exp(
                            1.0j
                            * np.mean(
                                np.angle(
                                    state[2 * j * 2 ** (n - i - 1) : (2 * j + 1) * 2 ** (n - i - 1)]
                                )
                            )
                        )
                        * np.linalg.norm(
                            state[2 * j * 2 ** (n - i - 1) : (2 * j + 1) * 2 ** (n - i - 1)]
                        ),
                        np.exp(
                            1.0j
                            * np.mean(
                                np.angle(
                                    state[
                                        (2 * j + 1)
                                        * 2 ** (n - i - 1) : (2 * j + 2)
                                        * 2 ** (n - i - 1)
                                    ]
                                )
                            )
                        )
                        * np.linalg.norm(
                            state[(2 * j + 1) * 2 ** (n - i - 1) : (2 * j + 2) * 2 ** (n - i - 1)]
                        ),
                    ]
                )
            )
            for j in range(2 ** i)
        ]
        prepare_multiplexed(
            circuit, qubits[:i], qubits[i], states, GRAY_CODE=GRAY_CODE, REVERSE_ZS=REVERSE_ZS
        )
    return circuit


def prepare_multiplexed(
    circuit, control_qubits, target_qubit, states, GRAY_CODE=True, REVERSE_ZS=True
):
    assert len(states) == 2 ** len(control_qubits)
    assert all(abs(np.linalg.norm(state) - 1.0) < 1e-8 for state in states)
    n = len(control_qubits)

    thetas = [2 * np.arccos(state[0].real) / np.pi for state in states]
    phis = [np.angle(state[1]) / np.pi for state in states]

    if GRAY_CODE:
        # Loading Gray code in bs
        bs = [[0]]
        nums = [0]
        for i in range(n):
            bs = [[0] + b for b in bs] + [[1] + b for b in reversed(bs)]
            nums += [x + 2 ** i for x in reversed(nums)]
    else:
        # Loading regular order of bitstrings in bs
        bs = [tuple(map(int, f"{i:0{n}b}")) for i in range(2 ** n)]
        nums = list(range(2 ** n))

    if REVERSE_ZS:
        # Implement multiplexed Ry
        for b, c in zip(bs[:-1], bs[1:]):
            theta = (
                sum((-1) ** sum(x * y for x, y in zip(b, d)) * thetas[j] for j, d in zip(nums, bs))
                / 2 ** n
            )
            # circuit.append(cirq.Y(target_qubit)**theta)
            circuit.ry(theta * np.pi, target_qubit)
            # circuit.append(cirq.CNOT(control_qubits[j], target_qubit) for j,(x,y) in enumerate(zip(b,c)) if x != y)
            for j, (x, y) in enumerate(zip(b, c)):
                if x != y:
                    circuit.cx(control_qubits[j], target_qubit)
        b = bs[-1]
        theta = (
            sum((-1) ** sum(x * y for x, y in zip(b, d)) * thetas[j] for j, d in enumerate(bs))
            / 2 ** n
        )
        # circuit.append(cirq.Y(target_qubit)**theta)
        circuit.ry(theta * np.pi, target_qubit)

        # Implement reverse of multiplexed Rz
        phi = (
            sum((-1) ** sum(x * y for x, y in zip(b, d)) * phis[j] for j, d in zip(nums, bs))
            / 2 ** n
        )
        # circuit.append(cirq.Z(target_qubit)**phi)
        circuit.rz(phi * np.pi, target_qubit)
        for c, b in zip(bs[-1:0:-1], bs[-2::-1]):
            # circuit.append(cirq.CNOT(control_qubits[j], target_qubit) for j,(x,y) in enumerate(zip(b,c)) if x != y)
            for j, (x, y) in enumerate(zip(b, c)):
                if x != y:
                    circuit.cx(control_qubits[j], target_qubit)
            phi = (
                sum((-1) ** sum(x * y for x, y in zip(b, d)) * phis[j] for j, d in zip(nums, bs))
                / 2 ** n
            )
            # circuit.append(cirq.Z(target_qubit)**phi)
            circuit.rz(phi * np.pi, target_qubit)
    else:
        # Implement multiplexed Ry
        for b, c in zip(bs, bs[1:] + [bs[0]]):
            theta = (
                sum((-1) ** sum(x * y for x, y in zip(b, d)) * thetas[j] for j, d in zip(nums, bs))
                / 2 ** n
            )
            # circuit.append(cirq.Y(target_qubit)**theta)
            circuit.ry(theta * np.pi, target_qubit)
            # circuit.append(cirq.CNOT(control_qubits[j], target_qubit) for j,(x,y) in enumerate(zip(b,c)) if x != y)
            for j, (x, y) in enumerate(zip(b, c)):
                if x != y:
                    circuit.cx(control_qubits[j], target_qubit)

        # Implement multiplexed Rz
        for b, c in zip(bs, bs[1:] + [bs[0]]):
            phi = (
                sum((-1) ** sum(x * y for x, y in zip(b, d)) * phis[j] for j, d in zip(nums, bs))
                / 2 ** n
            )
            # circuit.append(cirq.Z(target_qubit)**phi)
            circuit.rz(phi * np.pi, target_qubit)
            # circuit.append(cirq.CNOT(control_qubits[j], target_qubit) for j,(x,y) in enumerate(zip(b,c)) if x != y)
            for j, (x, y) in enumerate(zip(b, c)):
                if x != y:
                    circuit.cx(control_qubits[j], target_qubit)

    return circuit


if __name__ == "__main__":
    from qiskit import QuantumCircuit, execute, Aer

    n = 2
    state = normalize_and_remove_phase(np.random.rand(2 ** n) + 1.0j * np.random.rand(2 ** n))
    state /= np.linalg.norm(state)
    qubits = list(range(n))
    circuit = QuantumCircuit(len(qubits))
    Shende_Bullock_Markov(circuit, qubits, state)
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
