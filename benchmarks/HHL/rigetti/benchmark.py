import numpy as np

from libbench.rigetti import Benchmark as RigettiBenchmark

from .job import HHLJob
from .. import HHLBenchmarkMixin


class HHLBenchmarkBase(HHLBenchmarkMixin, RigettiBenchmark):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_jobs(self):
        yield from HHLJob.job_factory(
            self.matrix,
            self.num_shots,
            self.shots_multiplier,          
        )

    def __str__(self):
        return "Rigetti-HHL"


class HHLBenchmark(HHLBenchmarkBase):
    """
    Full Benchmark

    Either a cloud device, or a qasm_simulator, potentially with simulated noise
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def parse_result(self, job, result):
        """
        initially results are in the form qubit : measurement-outcomes
        {
            0: array([1, 0, 0, 1, 1, 1, 1, 0, 1, 0]),
            1: array([1, 0, 1, 1, 1, 0, 1, 0, 1, 0]),
            2: array([1, 0, 0, 1, 1, 1, 1, 0, 1, 0])
        }
        so each column represents one joint measurement outcome; selecting only a subset of the qubits
        effectively means measuring only a subset, ignoring the rest
        """        
        counts = {}
        qubits = job.num_qubits + 1
                  
        for measurement in np.vstack([result[k] for k in range(qubits)]).T:
            key = "".join(["0" if b == 0 else "1" for b in measurement])
            if key in counts:
                counts[key] += 1
            else:
                counts[key] = 1

        total = 0
        histogram = [0] * 2 ** (job.num_qubits-job.num_ancillas)
        for result in counts:
            total += counts[result]
            if result[0:2]=="01":
                histogram[int(result[2:], 2)] = counts[result]   

        return {"basis_vec": job.basis_vec, "histogram": histogram, "total": total}

class HHLSimulatedBenchmark(HHLBenchmarkBase):
    """
    Simulated HHL Benchmark

    The device behaves like a statevector_simulator, i.e. without noise
    """

    def __init__(self, *args, **kwargs):     
        super().__init__(*args, **kwargs)

    def parse_result(self, job, result):
        psi = result.amplitudes

        used_qubits = (job.num_qubits-job.num_ancillas)  

        histogram = []
        for i in range(2 ** used_qubits):
            j = i +  2**job.num_qubits - 2**used_qubits
            histogram.append(np.abs(psi[j]) ** 2)

        return {"basis_vec": job.basis_vec, "histogram": histogram, "total": 1}    
