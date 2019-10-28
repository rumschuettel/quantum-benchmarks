from abc import abstractmethod
from libbench.lib import print_hl
from libbench.link import VendorJob, VendorLink, ThinPromise
import functools
from qiskit.providers import JobStatus

IBM_KNOWN_STATEVECTOR_DEVICES = ["statevector_simulator"]

IBM_KNOWN_MEASURE_LOCAL_DEVICES = ["qasm_simulator"]


class IBMJob(VendorJob):
    def __init__(self):
        super().__init__()
        self.circuit = None
        self.device_info = None

    @abstractmethod
    def run(self, device):
        self.device_info = device.configuration().to_dict()

    def serialize(self):
        return {"circuit": self.circuit, "device_info": self.device_info}


class IBMThinPromise(ThinPromise):
    """
        Override mock status report to work with IBMJobManager
    """

    def status(self):
        return JobStatus.ERROR if self._result is None else JobStatus.DONE


class IBMLinkBase(VendorLink):
    def get_device_topology(self, name):
        return self.get_device(name).configuration().coupling_map


class IBMCloudLink(IBMLinkBase):
    def __init__(self):
        super().__init__()

        # load accounts
        from qiskit import IBMQ

        IBMQ.load_account()

        # check whether we have accounts
        providers = IBMQ.providers()
        assert len(providers) == 1, "no account loaded, or multiple accounts found."

        self.IBMQ_cloud = providers[0]

        print_hl("IBMQ cloud account loaded.")

    @functools.lru_cache()
    def get_devices(self):
        return {device.name(): device for device in self.IBMQ_cloud.backends()}


class IBMMeasureLocalLink(IBMLinkBase):
    def __init__(self):
        super().__init__()

        from qiskit import Aer

        self.IBMQ_local = Aer

        print_hl("qiskit Aer loaded.")

    @functools.lru_cache()
    def get_devices(self):
        return {
            device.name(): device
            for device in self.IBMQ_local.backends()
            if device.name() in IBM_KNOWN_MEASURE_LOCAL_DEVICES
        }


class IBMStatevectorLink(IBMLinkBase):
    def __init__(self):
        super().__init__()

        from qiskit import Aer

        self.IBMQ_local = Aer

        print_hl("qiskit Aer loaded.")

    @functools.lru_cache()
    def get_devices(self):
        return {
            device.name(): device
            for device in self.IBMQ_local.backends()
            if device.name() in IBM_KNOWN_STATEVECTOR_DEVICES
        }
