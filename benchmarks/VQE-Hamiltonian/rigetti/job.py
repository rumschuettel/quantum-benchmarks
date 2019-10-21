

from libbench.rigetti import Job as RigettiJob
from libbench import ThinPromise

from ..common import HamiltonianType, AnsatzCircuit

import pyquil as pq



class RigettiVQEHamiltonianSimulatedJob(RigettiJob):
    def __init__(self, qubits: int, J1: float, J2: float, type: HamiltonianType, **kwargs):
        super().__init__()
        self.J1 = J1
        self.J2 = J2

        if type == HamiltonianType.ISING:
            self.ansatz = AnsatzCircuit(qubits, 2, type)
        elif type == HamiltonianType.HEISENBERG:
            pass
        else:
            raise NotImplementedError()

        param_count = sum(1 for layer in self.ansatz for gate in layer if gate[0] == True)

        # build program
        program = pq.Program()
        thetas = program.declare('theta', memory_type='REAL', memory_size=param_count)

        param_idx = 0
        for layer in self.ansatz:
            for (parametrized, gate_name, *location) in layer:
                if parametrized:
                    theta = thetas[param_idx]
                    param_idx += 1

                    if gate_name == "Rx":
                        program += pq.gates.RX(theta, *location)
                    elif gate_name == "Ry":
                        program += pq.gates.RY(theta, *location)
                    elif gate_name == "Rz":
                        program += pq.gates.RZ(theta, *location)
                    else:
                        raise NotImplementedError("gate not implemented for VQE ansatz")

                else:
                    if gate_name == "CNOT":
                        program += pq.gates.CNOT(*location)
                    elif gate_name == "CZ":
                        program += pq.gates.CZ(*location)
                    else:
                        raise NotImplementedError("gate not implemented for VQE ansatz")

        self.program = program
                
    
    def run(self, device):
        pass

    def __str__(self):
        return f"RigettiVQEHamiltonianSimulatedJob-{self.J1}-{self.J2}"
