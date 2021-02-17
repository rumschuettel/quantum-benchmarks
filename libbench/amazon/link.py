from abc import ABC, abstractmethod
from libbench.lib import print_hl
from libbench.link import VendorLink, VendorJob

from .promise import AmazonMeasureLocalPromise

import braket, braket.circuits
import functools

class AmazonDevice(ABC):
    @abstractmethod
    def execute(self, circuit: braket.circuits.Circuit, num_shots: int):
        pass

class LocalSimulatorMeasureLocal(AmazonDevice):
    def __init__(self):
        self.name = "LocalSimulator"

    def execute(self, circuit, num_shots: int, **kwargs):
        return {
            "result": AmazonMeasureLocalPromise(circuit, braket.devices.LocalSimulator(), num_shots),
            "transpiled_circuit": None,
        }

class LocalSimulatorStatevector(AmazonDevice):
    def __init__(self):
        raise NotImplementedError()    


AMAZON_STATEVECTOR_DEVICES = {}
AMAZON_MEASURE_LOCAL_DEVICES = {"LocalSimulator"}
AMAZON_CLOUD_DEVICES = {}


class AmazonJob(VendorJob):
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


class AmazonLinkBase(VendorLink):
    def get_device_topology(self, name):
        return None


class AmazonCloudLink(AmazonLinkBase):
    def __init__(self):
        super().__init__()

        print_hl("AWS cloud backend loaded.")

    @functools.lru_cache()
    def get_devices(self):
        """
        Retrieves the cloud services of AWS.
        """
        return AMAZON_CLOUD_DEVICES


class AmazonMeasureLocalLink(AmazonLinkBase):
    def __init__(self):
        super().__init__()

        print_hl("AWS measure local backend loaded.")

    @functools.lru_cache()
    def get_devices(self):
        """
        Retrieves the measure local services of AWS.
        """
        return AMAZON_MEASURE_LOCAL_DEVICES


class AmazonStatevectorLink(AmazonLinkBase):
    def __init__(self):
        super().__init__()

        print_hl("AWS statevector simulator backend loaded.")

    @functools.lru_cache()
    def get_devices(self):
        """
        Retrieves the available statevector simulators in AWS.
        """
        return AMAZON_STATEVECTOR_DEVICES
