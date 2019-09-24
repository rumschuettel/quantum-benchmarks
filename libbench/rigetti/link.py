from libbench.link import VendorLink, VendorJob

import pyquil as pq

# with rigetti we can have any kind of qvm we want, and also other topologies etc
RIGETTI_EXTRA_QVMS = [nn for n in [8, 16, 24] for nn in [f"{n}q-qvm", f"{n}q-noisy-qvm"]]


class RigettiJob(VendorJob):
    pass


class RigettiLink(VendorLink):
    def __init__(self):
        super().__init__()

    def get_devices(self):
        return {
            n: pq.get_qc(n, as_qvm=False)
            for n in [*pq.list_quantum_computers(qpus=True, qvms=False), *RIGETTI_EXTRA_QVMS]
        }


class RigettiSimulatorLink(VendorLink):
    def get_devices(self):
        # any qpu device can also be used as a qvm for rigetti, so we include both
        return {
            n: pq.get_qc(n, as_qvm=True)
            for n in [*pq.list_quantum_computers(qpus=True, qvms=True), *RIGETTI_EXTRA_QVMS]
        }

    def __init__(self):
        super().__init__()
