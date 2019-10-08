from libbench.ibm import Benchmark as IBMBenchmark

from .job import IBMVQEHamiltonianJob
from .. import VQEHamiltonianBenchmarkMixin

class IBMVQEHamiltonianBenchmarkBase(VQEHamiltonianBenchmarkMixin, IBMBenchmark):
    pass

class IBMVQEHamiltonianSimulatedBenchmark(IBMVQEHamiltonianBenchmarkBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_jobs(self):
        yield IBMVQEHamiltonianJob(self.qubits, self.J1, self.J2, self.hamiltonian_type)

    def parse_result(self, job, result):
        return result['wavefunction'][0]

    def __str__(self):
        return "IBM-VQE-Hamiltonian"


class IBMVQEHamiltonianBenchmark(IBMVQEHamiltonianBenchmarkBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        raise NotImplementedError()
