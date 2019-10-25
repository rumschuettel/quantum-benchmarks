from abc import ABC, abstractmethod
from libbench.lib import print_hl
from libbench.link import VendorLink, VendorJob
from .promise import GoogleCloudPromise
from .promise import GoogleMeasureLocalPromise
from .promise import GoogleStatevectorPromise
import cirq
import functools


class GoogleDevice(ABC):
    @abstractmethod
    def execute(self, circuit: cirq.Circuit, num_shots: int):
        pass


class SparseSimulatorMeasureLocal(GoogleDevice):
    def __init__(self):
        self.name = "sparse_simulator_measure_local"

    def execute(self, circuit, num_shots: int):
        return GoogleMeasureLocalPromise(circuit, cirq.Simulator(), num_shots=num_shots)


class SparseSimulatorStatevector(GoogleDevice):
    def __init__(self):
        self.name = "sparse_simulator_statevector"

    def execute(self, circuit, num_shots: int, **kwargs):
        return GoogleStatevectorPromise(circuit, cirq.Simulator(), num_shots=num_shots, **kwargs)


GOOGLE_STATEVECTOR_DEVICES = {
    "sparse_simulator_statevector": SparseSimulatorStatevector()
    # support for the density matrix simulator can be added later if necessary
}

GOOGLE_MEASURE_LOCAL_DEVICES = {
    "sparse_simulator_measure_local": SparseSimulatorMeasureLocal()
}

GOOGLE_CLOUD_DEVICES = {}


class GoogleJob(VendorJob):
    def __init__(self):
        super().__init__()
        self.circuit = None

    def serialize(self):
        return self.circuit


class GoogleLinkBase(VendorLink):
    def get_device_topology(self, name):
        return None


class GoogleCloudLink(GoogleLinkBase):
    def __init__(self):
        super().__init__()

        print_hl("cirq cloud backend loaded.")

    @functools.lru_cache()
    def get_devices(self):
        """
            Retrieves the cloud services of Google.
        """
        return GOOGLE_CLOUD_DEVICES


class GoogleMeasureLocalLink(GoogleLinkBase):
    def __init__(self):
        super().__init__()

        print_hl("cirq measure local backend loaded.")

    @functools.lru_cache()
    def get_devices(self):
        """
            Retrieves the measure local services of Google.
        """
        return GOOGLE_MEASURE_LOCAL_DEVICES


class GoogleStatevectorLink(GoogleLinkBase):
    def __init__(self):
        super().__init__()

        print_hl("cirq statevector simulator backend loaded.")

    @functools.lru_cache()
    def get_devices(self):
        """
            Retrieves the available statevector simulators in cirq.
        """
        return GOOGLE_STATEVECTOR_DEVICES
