import numpy as np
import cirq


def normalize_and_remove_phase(v):
    return v / np.linalg.norm(v) / np.exp(1.0j * np.angle(v[0]))


def Shende_Bullock_Markov(state, qubits, GRAY_CODE=True, REVERSE_ZS=True):
    assert len(state) == 2 ** len(qubits)
    assert abs(np.linalg.norm(state) - 1.0) < 1e-8

    circuit = cirq.Circuit()
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
                                    state[
                                        2
                                        * j
                                        * 2 ** (n - i - 1) : (2 * j + 1)
                                        * 2 ** (n - i - 1)
                                    ]
                                )
                            )
                        )
                        * np.linalg.norm(
                            state[
                                2
                                * j
                                * 2 ** (n - i - 1) : (2 * j + 1)
                                * 2 ** (n - i - 1)
                            ]
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
                            state[
                                (2 * j + 1)
                                * 2 ** (n - i - 1) : (2 * j + 2)
                                * 2 ** (n - i - 1)
                            ]
                        ),
                    ]
                )
            )
            for j in range(2 ** i)
        ]
        circuit.append(
            prepare_multiplexed(
                states,
                qubits[:i],
                qubits[i],
                GRAY_CODE=GRAY_CODE,
                REVERSE_ZS=REVERSE_ZS,
            )
        )
    return circuit


def prepare_multiplexed(
    states, control_qubits, target_qubit, GRAY_CODE=True, REVERSE_ZS=True
):
    assert len(states) == 2 ** len(control_qubits)
    assert all(abs(np.linalg.norm(state) - 1.0) < 1e-8 for state in states)
    n = len(control_qubits)

    thetas = [2 * np.arccos(state[0].real) / np.pi for state in states]
    phis = [np.angle(state[1]) / np.pi for state in states]

    circuit = cirq.Circuit()

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
                sum(
                    (-1) ** sum(x * y for x, y in zip(b, d)) * thetas[j]
                    for j, d in zip(nums, bs)
                )
                / 2 ** n
            )
            circuit.append(cirq.Y(target_qubit) ** theta)
            circuit.append(
                cirq.CNOT(control_qubits[j], target_qubit)
                for j, (x, y) in enumerate(zip(b, c))
                if x != y
            )
        b = bs[-1]
        theta = (
            sum(
                (-1) ** sum(x * y for x, y in zip(b, d)) * thetas[j]
                for j, d in enumerate(bs)
            )
            / 2 ** n
        )
        circuit.append(cirq.Y(target_qubit) ** theta)

        # Implement reverse of multiplexed Rz
        phi = (
            sum(
                (-1) ** sum(x * y for x, y in zip(b, d)) * phis[j]
                for j, d in zip(nums, bs)
            )
            / 2 ** n
        )
        circuit.append(cirq.Z(target_qubit) ** phi)
        for c, b in zip(bs[-1:0:-1], bs[-2::-1]):
            circuit.append(
                cirq.CNOT(control_qubits[j], target_qubit)
                for j, (x, y) in enumerate(zip(b, c))
                if x != y
            )
            phi = (
                sum(
                    (-1) ** sum(x * y for x, y in zip(b, d)) * phis[j]
                    for j, d in zip(nums, bs)
                )
                / 2 ** n
            )
            circuit.append(cirq.Z(target_qubit) ** phi)
    else:
        # Implement multiplexed Ry
        for b, c in zip(bs, bs[1:] + [bs[0]]):
            theta = (
                sum(
                    (-1) ** sum(x * y for x, y in zip(b, d)) * thetas[j]
                    for j, d in zip(nums, bs)
                )
                / 2 ** n
            )
            circuit.append(cirq.Y(target_qubit) ** theta)
            circuit.append(
                cirq.CNOT(control_qubits[j], target_qubit)
                for j, (x, y) in enumerate(zip(b, c))
                if x != y
            )

        # Implement multiplexed Rz
        for b, c in zip(bs, bs[1:] + [bs[0]]):
            phi = (
                sum(
                    (-1) ** sum(x * y for x, y in zip(b, d)) * phis[j]
                    for j, d in zip(nums, bs)
                )
                / 2 ** n
            )
            circuit.append(cirq.Z(target_qubit) ** phi)
            circuit.append(
                cirq.CNOT(control_qubits[j], target_qubit)
                for j, (x, y) in enumerate(zip(b, c))
                if x != y
            )

    return circuit


if __name__ == "__main__":
    n = 3
    state = normalize_and_remove_phase(
        np.random.rand(2 ** n) + 1.0j * np.random.rand(2 ** n)
    )
    qubits = [cirq.GridQubit(0, i) for i in range(n)]
    circuit = Shende_Bullock_Markov(state, qubits, True, True)
    print(circuit)
    final_state = cirq.Simulator().simulate(circuit, qubit_order=qubits).final_state
    inp = np.sum(np.conj(final_state.T) * state)
    print(abs(abs(inp) - 1.0))
