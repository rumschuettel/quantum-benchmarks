from abc import ABC, abstractmethod, abstractproperty
from libbench.link import VendorLink, VendorJob, ThinPromise
from typing import Union, Tuple, List

import pyquil as pq

import functools


class RigettiDevice(ABC):
    @abstractmethod
    def execute(self, program: pq.Program, num_shots: int):
        pass

    @abstractproperty
    def name(self):
        pass

    @abstractproperty
    def info(self):
        pass


class RigettiQVM(RigettiDevice):
    def __init__(self, device_name: str):
        self.device = pq.get_qc(device_name, as_qvm=True)

    @property
    def name(self):
        return self.device.name

    @property
    def info(self):
        return self.device.device.get_specs().to_dict()

    def _run_and_measure(self, program: pq.Program, num_shots: int, optimize):
        program = program.copy()
        qubits = program.get_qubits()

        # add measurements everywhere
        ro = program.declare("ro", "BIT", len(qubits))
        for i, q in enumerate(qubits):
            program.inst(pq.gates.MEASURE(q, ro[i]))

        program.wrap_in_numshots_loop(shots=num_shots)

        executable = self.device.compile(program, optimize=optimize)

        # try:
        bitstring_array = self.device.run(executable=executable)
        # except:  # TODO be more specific
        #    return None

        bitstring_dict = {}
        for i, q in enumerate(qubits):
            bitstring_dict[q] = bitstring_array[:, i]

        return bitstring_dict

    def execute(self, program: pq.Program, num_shots: int, optimize=True):
        return ThinPromise(
            self._run_and_measure,
            program=program,
            num_shots=num_shots,
            optimize=optimize,
        )


class RigettiQPU(RigettiQVM):
    def __init__(self, device_name: str):
        # not calling super().__init__() on purpose
        self.device = pq.get_qc(device_name, as_qvm=False)


class RigettiStatevectorSimulator(RigettiDevice):
    def __init__(self):
        self.device = pq.api.WavefunctionSimulator()

    @property
    def name(self):
        return "WavefunctionSimulator"

    @property
    def info(self):
        return None
        
    def execute(self, program: pq.Program, **_):
        return ThinPromise(self.device.wavefunction, program)


# with rigetti we can have any kind of qvm we want, and also other topologies etc
RIGETTI_EXTRA_QVMS = [
    nn for n in [2, 4, 8, 16, 24] for nn in [f"{n}q-qvm", f"{n}q-noisy-qvm"]
]


class RigettiJob(VendorJob):
    def __init__(self):
        super().__init__()
        self.program = None
        self.device_info = None

    def serialize(self):
        return {
            "program": self.program,
            "device_info": self.device_info
        }

    @abstractmethod
    def run(self, device: RigettiDevice):
        self.device_info = device.info


class RigettiCloudLink(VendorLink):
    def __init__(self):
        super().__init__()

    @functools.lru_cache()
    def get_devices(self):
        devices = {}
        for n in pq.list_quantum_computers(qpus=True, qvms=False):
            try:
                devices[n] = RigettiQPU(n)
            except RuntimeError:
                pass
        return devices

    def get_device_topology(self, name) -> List[Tuple[int, int]]:
        # .qubit_topology() returns a networkx graph
        return list(self.get_device(name).device.qubit_topology().edges())


class RigettiMeasureLocalLink(VendorLink):
    def __init__(self):
        super().__init__()

    @functools.lru_cache()
    def get_devices(self):
        # any qpu device can also be used as a qvm for rigetti, so we include both
        return {
            n: RigettiQVM(n)
            for n in [
                *pq.list_quantum_computers(qpus=True, qvms=True),
                *RIGETTI_EXTRA_QVMS,
            ]
        }

    def get_device_topology(self, name) -> List[Tuple[int, int]]:
        # .qubit_topology() returns a networkx graph
        return list(self.get_device(name).device.qubit_topology().edges())


class RigettiStatevectorLink(VendorLink):
    def __init__(self):
        super().__init__()

    def get_devices(self):
        return {"WavefunctionSimulator": RigettiStatevectorSimulator()}

    def get_device_topology(self, name) -> None:
        return None
