#!/usr/bin/env python3

from benchmarks.HHL.ibm import job
from benchmarks.HHL.matrices import MATRICES

from libbench import print_hl

import qiskit
import numpy as np
import itertools
from tqdm import tqdm


def reshuffle_qubits(unitary: np.array, permutation: list) -> np.array:
    """
    same effect as adding swap gates to achieve a permutation of the unitary
    example:

    reshuffle_qubits(
        np.array([
            [1, 2, 0, 0],
            [3, 4, 0, 0],
            [0, 0, 5, 6],
            [0, 0, 7, 8]
        ]), [1, 0]) == np.array([
            [1, 0, 2, 0],
            [0, 5, 0, 6],
            [3, 0, 4, 0],
            [0, 7, 0, 8]
        ])
    """
    n_qubits = int(np.log2(unitary.shape[0]))
    unitary = unitary.reshape([2] * 2 * n_qubits)
    unitary = unitary.transpose(permutation + tuple(p + n_qubits for p in permutation))
    return unitary.reshape(2 ** n_qubits, -1)


def partial_transpose(unitary: np.array, qubits_to_pair_off: int) -> np.array:
    """
    performs a partial transpose of a tensor
    A[i1,i2,...in ; j1,j2,...jn] -> A[i1,j1,i2,j2, ...in,jn]
    and then reshapes to a matrix where the first m=qubits_to_pair_off pairs of indices are on the left, i.e.
    -> A[i1,j1,...,im,jm ; i(m+1),j(m+1), ..., in,jn]
    """
    n_qubits = int(np.log2(unitary.shape[0]))
    assert (
        0 < qubits_to_pair_off < n_qubits
    ), f"qubits to pair off must be at least 1 and att most {n_qubits}"

    unitary = unitary.reshape([2] * 2 * n_qubits)
    pt_indices = [(i, n_qubits + i) for i in range(n_qubits)]
    pt_indices = tuple(i for pair in pt_indices for i in pair)
    pt_operator = unitary.transpose(pt_indices)
    return pt_operator.reshape(2 ** (2 * qubits_to_pair_off), -1)


def _partition_str(permutation: tuple, qubits_to_pair_off: int) -> str:
    return (
        "".join(str(p) for p in permutation[:qubits_to_pair_off])
        + " "
        + "".join(str(p) for p in permutation[qubits_to_pair_off:])
    )


def subsets_k(collection, k):
    yield from partition_k(collection, k, k)


def partition_k(collection, min, k):
    if len(collection) == 1:
        yield [collection]
        return
    first = collection[0]
    for smaller in partition_k(collection[1:], min - 1, k):
        if len(smaller) > k:
            continue
        if len(smaller) >= min:
            for n, subset in enumerate(smaller):
                yield smaller[:n] + [[first] + subset] + smaller[n + 1 :]
        if len(smaller) < k:
            yield [[first]] + smaller


def test_matrices(verbose: bool = False):
    for name, mdata in MATRICES.items():
        n_qubits = mdata["qubits"]
        print_hl(f"checking {name} on {n_qubits} qubits")
        circuit = job.HHLJob.list_to_circuit(mdata["circuit"], qiskit.QuantumCircuit(n_qubits))

        # inbuilt checks
        print(f"qiskit num_connected_components() = {circuit.num_connected_components()}")
        print(f"qiskit num_unitary_factors()      = {circuit.num_unitary_factors()}")

        # get unitary
        unitary = (
            qiskit.execute(circuit, backend=qiskit.providers.aer.UnitarySimulator())
            .result()
            .get_unitary()
        )

        # check rank for all permutations
        partitions = list(subsets_k(list(range(n_qubits)), 2))
        print(f"checking tensor rank across all {len(partitions)} partitions...")

        min_rank = np.inf
        min_partition_str = []

        for sa, sb in tqdm(partitions):
            permutation = tuple(sa + sb)
            permuted_unitary = reshuffle_qubits(unitary, permutation)

            qubits_to_pair_off = len(sa)
            pt_operator = partial_transpose(permuted_unitary, qubits_to_pair_off)
            rank = np.linalg.matrix_rank(pt_operator)
            ps = _partition_str(permutation, qubits_to_pair_off)

            if rank <= min_rank:
                min_rank = rank
                min_partition_str.append(ps)

        print_hl(
            f"minimum rank = {min_rank} reached on {len(min_partition_str)} partitions\n",
            color="cyan" if min_rank > 1 else "red",
        )
        verbose and print(min_partition_str)


if __name__ == "__main__":
    test_matrices()
