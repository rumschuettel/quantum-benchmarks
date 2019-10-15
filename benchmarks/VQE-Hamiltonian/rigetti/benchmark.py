from libbench.rigetti import Benchmark as RigettiBenchmark

from .job import RigettiVQEHamiltonianSimulatedJob
from .. import VQEHamiltonianBenchmarkMixin

class RigettiVQEHamiltonianBenchmarkBase(VQEHamiltonianBenchmarkMixin, RigettiBenchmark):
    pass

class RigettiVQEHamiltonianSimulatedBenchmark(RigettiVQEHamiltonianBenchmarkBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_jobs(self):
        yield RigettiVQEHamiltonianSimulatedJob(self.qubits, self.J1, self.J2, self.hamiltonian_type)

    def parse_result(self, job, result):
        return {
            "c,wv": result['wavefunction'][0],
            "c,e": result["energy"]
        }

    def __str__(self):
        return "Rigetti-VQE-Hamiltonian-Simulated"
