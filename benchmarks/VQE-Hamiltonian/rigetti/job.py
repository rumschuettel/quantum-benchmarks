from libbench.rigetti import Job as RigettiJob
from libbench import ThinPromise

from ..common import HamiltonianType

class RigettiVQEHamiltonianSimulatedJob(RigettiJob):
    def __init__(self, qubits: int, J1: float, J2: float, type: HamiltonianType, **kwargs):
        super().__init__()
        self.J1 = J1
        self.J2 = J2

        if type == HamiltonianType.ISING:
            pass
        elif type == HamiltonianType.HEISENBERG:
            pass
        else:
            raise NotImplementedError()
    
    def run(self, device):
        pass

    def __str__(self):
        return f"RigettiVQEHamiltonianSimulatedJob-{self.J1}-{self.J2}"
