from libbench.ibm import Benchmark as IBMBenchmark

from .job import IBMVQEHamiltonianSimulatedJob, IBMVQEHamiltonianJob
from .. import VQEHamiltonianBenchmarkMixin


class IBMVQEHamiltonianBenchmarkBase(VQEHamiltonianBenchmarkMixin, IBMBenchmark):
    pass


class IBMVQEHamiltonianSimulatedBenchmark(IBMVQEHamiltonianBenchmarkBase):
    def get_jobs(self):
        yield IBMVQEHamiltonianSimulatedJob(self.qubits, self.J1, self.J2, self.hamiltonian_type)

    def parse_result(self, job, result):
        return {"c,wv": result["wavefunction"][0], "c,e": result["energy"]}

    def __str__(self):
        return "IBM-VQE-Hamiltonian-Simulated"


class IBMVQEHamiltonianBenchmark(IBMVQEHamiltonianBenchmarkBase):
    def __init__(self, depth, rounds, **kwargs):
        super().__init__(**kwargs)

        self.depth = depth
        self.rounds = rounds

    def get_jobs(self):
        yield IBMVQEHamiltonianJob(
            self.depth,
            self.rounds,
            self.qubits,
            self.J1,
            self.J2,
            self.hamiltonian_type,
        )

    def parse_result(self, job, result):
        return {
            "c,wv": result["c"]["wavefunction"][0],
            "c,e": result["c"]["energy"],
            "q,wv": result["q"]["min_vector"],
            "q,e": result["q"]["energy"],
        }

    def __str__(self):
        return "IBM-VQE-Hamiltonian"
