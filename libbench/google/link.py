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
        return {
            "result": GoogleMeasureLocalPromise(circuit, cirq.Simulator(), num_shots=num_shots),
            "transpiled_circuit": None,
        }


class SparseSimulatorStatevector(GoogleDevice):
    def __init__(self):
        self.name = "sparse_simulator_statevector"

    def execute(self, circuit, num_shots: int, **kwargs):
        return {
            "result": GoogleStatevectorPromise(
                circuit, cirq.Simulator(), num_shots=num_shots, **kwargs
            ),
            "transpiled_circuit": None,
        }


GOOGLE_STATEVECTOR_DEVICES = {
    "sparse_simulator_statevector": SparseSimulatorStatevector()
    # support for the density matrix simulator can be added later if necessary
}

GOOGLE_MEASURE_LOCAL_DEVICES = {"sparse_simulator_measure_local": SparseSimulatorMeasureLocal()}

GOOGLE_CLOUD_DEVICES = {}


class GoogleJob(VendorJob):
    def __init__(self):
        super().__init__()
        self.circuit = None
        self.device_info = None

    def serialize(self):
        info = super().serialize()
        info.update({"circuit": self.circuit})
        return info

    def run(self, device):
        self.device_info = None

    def qasm(self):
        return self.circuit.to_qasm()


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
