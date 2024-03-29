from abc import ABC, abstractmethod
from libbench.lib import print_hl
from libbench.link import VendorLink, VendorJob

from .promise import AmazonMeasureLocalPromise, AmazonCloudPromise

import braket, braket.circuits, braket.devices, braket.aws
import functools


class AmazonDevice(ABC):
    @abstractmethod
    def execute(self, circuit: braket.circuits.Circuit, num_shots: int):
        pass


class CloudDevice(AmazonDevice):
    def __init__(self, name: str, address: str):
        self.name = name
        self.address = address

    def execute(self, circuit, num_shots: int, **kwargs):
        print_hl(circuit, color="white")
        return {
            "result": AmazonCloudPromise(circuit, braket.aws.AwsDevice(self.address), num_shots),
            "transpiled_circuit": None,
        }


class LocalSimulatorMeasureLocal(AmazonDevice):
    def __init__(self):
        self.name = "LocalSimulator"

    def execute(self, circuit, num_shots: int, **kwargs):
        return {
            "result": AmazonMeasureLocalPromise(
                circuit, braket.devices.LocalSimulator(), num_shots
            ),
            "transpiled_circuit": None,
        }


class LocalSimulatorStatevector(AmazonDevice):
    def __init__(self):
        raise NotImplementedError()


AMAZON_STATEVECTOR_DEVICES = {}
AMAZON_MEASURE_LOCAL_DEVICES = {"LocalSimulator": LocalSimulatorMeasureLocal()}
AMAZON_CLOUD_DEVICES = {
    "SV1": CloudDevice(name="SV1", address="arn:aws:braket:::device/quantum-simulator/amazon/sv1"),
    "Aspen-9": CloudDevice(name="Aspen-9", address="arn:aws:braket:::device/qpu/rigetti/Aspen-9"),
    "IonQ": CloudDevice(name="IonQ", address="arn:aws:braket:::device/qpu/ionq/ionQdevice"),
}


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
        self.device_info = device.properties if hasattr(device, "properties") else None

    def qasm(self):
        return str(self.circuit.to_ir().json())


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
