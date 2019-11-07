from abc import abstractmethod
from libbench.lib import print_hl
from libbench.link import VendorJob, VendorLink, ThinPromise
import functools
from qiskit.providers import JobStatus
import qiskit
from typing import Union, Tuple, List, Dict

IBM_KNOWN_STATEVECTOR_DEVICES = ["statevector_simulator"]

IBM_KNOWN_MEASURE_LOCAL_DEVICES = ["qasm_simulator"]


class IBMDevice:
    def __init__(self, device):
        self.device = device

    def execute(
        self,
        cirquit: qiskit.QuantumCircuit,
        num_shots=1024,
        initial_layout=None,
        optimization_level=3,
    ):
        experiment = qiskit.compiler.transpile(
            cirquit,
            initial_layout=initial_layout,
            optimization_level=optimization_level,
            backend=self.device,
        )
        print_hl(cirquit, color="grey")
        print_hl(experiment, color="grey")
        qobj = qiskit.compiler.assemble(
            experiment, shots=num_shots, max_credits=15, backend=self.device
        )
        return {"result": self.device.run(qobj), "transpiled_circuit": experiment}


class IBMJob(VendorJob):
    def __init__(self):
        super().__init__()
        self.circuit = None

    @abstractmethod
    def run(self, device):
        device = device.device
        self.device_info = {}
        if device.configuration() is not None:
            self.device_info["configuration"] = device.configuration().to_dict()
        if device.properties() is not None:
            self.device_info["properties"] = device.configuration().to_dict()

    def serialize(self):
        info = super().serialize()
        info.update({"circuit": self.circuit})
        return info


class IBMThinPromise(ThinPromise):
    """
        Override mock status report to work with IBMJobManager
    """

    def status(self):
        return JobStatus.ERROR if self._result is None else JobStatus.DONE


class IBMLinkBase(VendorLink):
    def get_device_topology(self, name) -> Union[Dict[Tuple[int, int], float], None]:
        device = self.get_device(name).device
        edges = [tuple(e) for e in device.configuration().coupling_map]

        topology = {}

        if device.properties() is not None:
            gates_cx = {
                tuple(g.qubits): g
                for g in device.properties().gates
                if g.gate == "cx" and any(param.name == "gate_error" for param in g.parameters)
            }
            gates_h = {
                g.qubits[0]: g
                for g in device.properties().gates
                if g.gate == "u3" and any(param.name == "gate_error" for param in g.parameters)
            }
            for e in edges:
                if not e in gates_cx:
                    topology[e] = 1.0
                else:
                    # we already ensured the parameter exists above
                    error_param = [p for p in gates_cx[e].parameters if p.name == "gate_error"][0]
                    topology[e] = 1.0 - error_param.value

                # reverse edge: weigh by four hadamards
                # we probably overestimate the error slightly by assuming an u3 gate
                a, b = e
                topology[(b, a)] = topology[(a, b)]
                if a in gates_h:
                    error_param = [p for p in gates_h[a].parameters if p.name == "gate_error"][0]
                    topology[e] -= 2 * error_param.value
                if b in gates_h:
                    error_param = [p for p in gates_h[b].parameters if p.name == "gate_error"][0]
                    topology[e] -= 2 * error_param.value

        else:
            for a, b in edges:
                topology[(a, b)] = 1.0
                topology[(b, a)] = 1.0

        return topology


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
        return {device.name(): IBMDevice(device) for device in self.IBMQ_cloud.backends()}


class IBMMeasureLocalLink(IBMLinkBase):
    def __init__(self):
        super().__init__()

        from qiskit import Aer

        self.IBMQ_local = Aer

        print_hl("qiskit Aer loaded.")

    @functools.lru_cache()
    def get_devices(self):
        return {
            device.name(): IBMDevice(device)
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
            device.name(): IBMDevice(device)
            for device in self.IBMQ_local.backends()
            if device.name() in IBM_KNOWN_STATEVECTOR_DEVICES
        }
