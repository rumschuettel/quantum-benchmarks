from ..link import VendorLink, VendorJob
from ..lib import print_hl

from qiskit import IBMQ, Aer


class IBMJob(VendorJob):
    pass


class IBMLink(VendorLink):
    def __init__(self):
        super().__init__()

        # load accounts
        IBMQ.load_account()

        # check whether we have accounts
        providers = IBMQ.providers()
        assert len(providers) == 1, "no account loaded, or multiple accounts found."

        self.IBMQ_cloud = providers[0]

        print_hl("IBMQ cloud account loaded.")


    def list_devices(self):
        return self.IBMQ_cloud.backends()


    def run(self, job: IBMJob):
        pass



class IBMSimulatorLink(VendorLink):
    def __init__(self):
        super().__init__()

        self.IBMQ_local = Aer

        print_hl("qiskit Aer loaded.")

    
    def list_devices(self):
        return self.IBMQ_local.backends()


    def run(self, job: IBMJob):
        pass