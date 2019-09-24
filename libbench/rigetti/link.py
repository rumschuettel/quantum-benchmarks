from libbench.link import VendorLink

import pyquil as pq


class RigettiLink(VendorLink):
    def get_devices(self):
        return pq.list_quantum_computers(qpus=True, qvms=False)

    def __init__(self):
        super().__init__()

        from pyquil.gates import CNOT, Z

        # to run on real device, change as_qvm=False
        qvm = pq.get_qc("Aspen-4-13Q-C", as_qvm=True)
        prog = pq.Program(Z(0), CNOT(0, 1))

        results = qvm.run_and_measure(prog, trials=10)
        print(results)


class RigettiSimulatorLink(VendorLink):
    def get_devices(self):
        # any qpu device can also be used as a qvm for rigetti, so we include both
        return pq.list_quantum_computers(qpus=True, qvms=True)

    def __init__(self):
        super().__init__()
