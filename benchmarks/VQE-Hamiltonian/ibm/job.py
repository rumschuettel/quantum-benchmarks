from qiskit.aqua.operators import WeightedPauliOperator
from qiskit.aqua.algorithms import ExactEigensolver
from qiskit.aqua import run_algorithm
from qiskit.aqua.input import EnergyInput

from libbench.ibm import Job as IBMJob
from libbench.ibm import IBMThinPromise

from ..common import HamiltonianType


def Paulis_TIM_NN(N, Γ, J=0.5):
    terms = {
        "paulis": [
            list(
                h
                for h in [
                    {"label": "I" * i + "ZZ" + "I" * (N - i - 2), "coeff": {"real": J, "imag": 0}}
                ]
            )
            for i in range(0, N - 1)
        ]
        + [
            list(
                h
                for h in [
                    {"label": "I" * i + "X" + "I" * (N - i - 1), "coeff": {"real": -Γ, "imag": 0}}
                ]
            )
            for i in range(0, N)
        ]
    }
    terms["paulis"] = [h for hh in terms["paulis"] for h in hh]

    return WeightedPauliOperator.from_dict(terms)


def Paulis_Heisenberg_NNN(N, J2, J1=1.0):
    terms = {
        "paulis": [
            list(
                h
                for h in [
                    {"label": "I" * i + "XX" + "I" * (N - i - 2), "coeff": {"real": J1, "imag": 0}},
                    {"label": "I" * i + "YY" + "I" * (N - i - 2), "coeff": {"real": J1, "imag": 0}},
                    {"label": "I" * i + "ZZ" + "I" * (N - i - 2), "coeff": {"real": J1, "imag": 0}},
                ]
            )
            for i in range(0, N - 1)
        ]
        + [
            list(
                h
                for h in [
                    {
                        "label": "I" * i + "XIX" + "I" * (N - i - 3),
                        "coeff": {"real": J2, "imag": 0},
                    },
                    {
                        "label": "I" * i + "YIY" + "I" * (N - i - 3),
                        "coeff": {"real": J2, "imag": 0},
                    },
                    {
                        "label": "I" * i + "ZIZ" + "I" * (N - i - 3),
                        "coeff": {"real": J2, "imag": 0},
                    },
                ]
            )
            for i in range(0, N - 2)
        ]
    }
    terms["paulis"] = [h for hh in terms["paulis"] for h in hh]

    return WeightedPauliOperator.from_dict(terms)


class IBMVQEHamiltonianSimulatedJob(IBMJob):
    def __init__(self, qubits: int, J1: float, J2: float, type: HamiltonianType, **kwargs):
        super().__init__()
        self.J1 = J1
        self.J2 = J2

        if type == HamiltonianType.ISING:
            self.operator = Paulis_TIM_NN(qubits, Γ=J1, J=J2)
        elif type == HamiltonianType.HEISENBERG:
            self.operator = Paulis_Heisenberg_NNN(qubits, J2=J2, J1=J1)
        else:
            raise NotImplementedError()

    def run(self, device):
        super().run(device)
        exact_eigensolver = ExactEigensolver(self.operator)
        return IBMThinPromise(exact_eigensolver.run)

    def __str__(self):
        return f"IBMVQEHamiltonianSimulatedJob-{self.J1}-{self.J2}"


class IBMVQEHamiltonianJob(IBMVQEHamiltonianSimulatedJob):
    @staticmethod
    def AquaCfgDict(depth, rounds, method="SLSQP", optimizer_rounds_name="maxiter"):
        return {
            "algorithm": {"name": "VQE", "operator_mode": "matrix"},
            "variational_form": {"name": "RYRZ", "depth": rounds, "entanglement": "full"},
            "optimizer": {"name": method, optimizer_rounds_name: rounds},
            "backend": {"name": "statevector_simulator", "provider": "qiskit.BasicAer"},
        }

    def __init__(self, depth, rounds, *args):
        super().__init__(*args)
        self.depth = depth
        self.rounds = rounds

    def run(self, device):
        super().run(device)
        result_q = run_algorithm(
            self.AquaCfgDict(self.depth, self.rounds), EnergyInput(self.operator)
        )
        result_cl = super().run(device)

        return IBMThinPromise(lambda: {"q": result_q, "c": result_cl.result()})

    def __str__(self):
        return f"IBMVQEHamiltonianJob-{self.J1}-{self.J2}"
