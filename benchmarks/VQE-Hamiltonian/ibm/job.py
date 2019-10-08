from qiskit.aqua.operators import WeightedPauliOperator
from qiskit.aqua.algorithms import ExactEigensolver

from libbench.ibm import Job as IBMJob
from libbench.ibm import IBMThinPromise

from ..common import HamiltonianType

def Paulis_TIM_NN(N, Γ, J=.5):
    terms = {
        'paulis': [
            list(h for h in [
                {'label': 'I'*i + 'ZZ' + 'I'*(N-i-2), 'coeff': {'real': J, 'imag': 0}}
            ])
            for i in range(0, N-1)
        ] + [
            list(h for h in [
                {'label': 'I'*i + 'X' + 'I'*(N-i-1), 'coeff': {'real': -Γ, 'imag': 0}}
            ])
            for i in range(0, N)
        ]
    }
    terms['paulis'] = [ h for hh in terms['paulis'] for h in hh ]
    
    return WeightedPauliOperator.from_dict(terms)


def Paulis_Heisenberg_NNN(N, J2, J1=1.):
    terms = {
        'paulis': [
            list(h for h in [
                {'label': 'I'*i + 'XX' + 'I'*(N-i-2), 'coeff': {'real': J1, 'imag': 0}},
                {'label': 'I'*i + 'YY' + 'I'*(N-i-2), 'coeff': {'real': J1, 'imag': 0}},
                {'label': 'I'*i + 'ZZ' + 'I'*(N-i-2), 'coeff': {'real': J1, 'imag': 0}}
            ])
            for i in range(0, N-1)
        ] + [
            list(h for h in [
                {'label': 'I'*i + 'XIX' + 'I'*(N-i-3), 'coeff': {'real': J2, 'imag': 0}},
                {'label': 'I'*i + 'YIY' + 'I'*(N-i-3), 'coeff': {'real': J2, 'imag': 0}},
                {'label': 'I'*i + 'ZIZ' + 'I'*(N-i-3), 'coeff': {'real': J2, 'imag': 0}}
            ])
            for i in range(0, N-2)
        ]
    }
    terms['paulis'] = [ h for hh in terms['paulis'] for h in hh ]
    
    return WeightedPauliOperator.from_dict(terms)



class IBMVQEHamiltonianJob(IBMJob):
    def __init__(self, qubits: int, J1: float, J2: float, type: HamiltonianType):
        self.J1 = J1
        self.J2 = J2

        if type == HamiltonianType.ISING:
            self.operator = Paulis_TIM_NN(qubits, Γ=J1, J=J2)
        elif type == HamiltonianType.HEISENBERG:
            self.operator = Paulis_Heisenberg_NNN(qubits, J2=J2, J1=J1)
        else:
            raise NotImplementedError()
    
    def run(self, device):
        exact_eigensolver = ExactEigensolver(self.operator)
        return IBMThinPromise(exact_eigensolver.run)

    def __str__(self):
        return f"IBMVQEHamiltonianJob-{self.J1}-{self.J2}"