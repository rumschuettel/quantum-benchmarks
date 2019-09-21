from libbench.link import VendorLink

import pyquil as pq


class RigettiLink(VendorLink):
    def get_devices():
        return pq.list_quantum_computers()

    def __init__(self):
        super().__init__()

        from pyquil.gates import CNOT, Z

        # to run on real device, change as_qvm=False
        qvm = pq.get_qc("9q-square", as_qvm=True)
        prog = pq.Program(Z(0), CNOT(0, 1))

        results = qvm.run_and_measure(prog, trials=10)
        print(results)
