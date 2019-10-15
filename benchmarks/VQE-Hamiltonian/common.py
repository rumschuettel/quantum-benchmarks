from enum import Enum
from pathlib import Path
from typing import Dict

from libbench import VendorJob

from matplotlib import pyplot as plt
import numpy as np

from .qubism import qubism_plot

class HamiltonianType(Enum):
    HEISENBERG = 1
    ISING = 2


def AnsatzCircuit(qubits: int, depth: int, hamiltonian_type: HamiltonianType):
    layers = []
    for l in range(depth):
        # parametrized 1-qubit rotations
        layers.append([
            (True, "Rz", i) for i in range(qubits)
        ])
        # alternating layer of unparametrized CNOT's
        layers.append([
            (False, "CNOT", i, i+1) for i in range(l%2, qubits-1, 2)
        ])
    return layers


class VQEHamiltonianBenchmarkMixin:
    def __init__(self, hamiltonian_type: str, qubits: int, J1: float, J2: float, **_):
        self.hamiltonian_type = HamiltonianType[hamiltonian_type]
        self.qubits = qubits
        self.J1 = J1
        self.J2 = J2

    def collate_results(self, results: Dict[VendorJob, object], path: Path):
        return results

    def visualize(self, collated_result: object, path: Path) -> Path:
        for job in collated_result:
            wv = collated_result[job]

            fig = qubism_plot(wv["c,wv"], wv["q,wv"]-wv["c,wv"] if "q,wv" in wv else None)
            fig.savefig(path / f"plot-{job}.pdf")


def argparser(toadd, **argparse_options):
    parser = toadd.add_parser(
        "VQE-Hamiltonian",
        help="VQE Hamiltonian Ground State Benchmark",
        **argparse_options,
    )
    parser.add_argument(
        "--hamiltonian_type",
        default=HamiltonianType.ISING.name,
        help=f"Which Hamiltonian to simulate. One of {', '.join(t.name for t in HamiltonianType)}"
    )
    parser.add_argument(
        "--qubits",
        default=6,
        type=int,
        help="How many qubits the Hamiltonian is defined on"
    )
    parser.add_argument(
        "--J1",
        default=1.,
        type=float,
        help="First coupling constant"
    )
    parser.add_argument(
        "--J2",
        default=1.,
        type=float,
        help="Second coupling constant"
    )
    parser.add_argument(
        "--depth",
        default=2,
        type=int,
        help="VQE ansatz circuit depth"
    )
    parser.add_argument(
        "--rounds",
        default=500,
        type=int,
        help="VQE training rounds"
    )
    return parser