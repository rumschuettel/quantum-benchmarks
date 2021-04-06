from abc import abstractmethod
from libbench.lib import print_hl
from libbench.link import VendorJob, VendorLink, ThinPromise
import functools
from qiskit.providers import JobStatus
import qiskit
from typing import Union, Tuple, List, Dict
from libbench import print_stderr
from qiskit.exceptions import QiskitError

IBM_KNOWN_STATEVECTOR_DEVICES = ["statevector_simulator"]

IBM_KNOWN_MEASURE_LOCAL_DEVICES = ["qasm_simulator"]


class IBMDevice:
    def __init__(self, device):
        self.device = device

    def execute(
        self,
        circuit: qiskit.QuantumCircuit,
        num_shots=1024,
        initial_layout=None,
        optimization_level=3,
    ):
        while optimization_level >= 0:
            try:
                experiment = qiskit.compiler.transpile(
                    circuit,
                    initial_layout=initial_layout,
                    optimization_level=optimization_level,
                    backend=self.device,
                )
                break
            except qiskit.transpiler.exceptions.TranspilerError as e:
                print_stderr("transpiler error. Lowering optimization level")
                optimization_level -= 1
                if optimization_level < 0:
                    raise e

        print_hl(circuit, color="white")
        print_hl(experiment, color="white")
        qobj = qiskit.compiler.assemble(
            experiment, shots=num_shots, max_credits=15, backend=self.device
        )

        try:
            return {"result": self.device.run(qobj), "transpiled_circuit": experiment}
        except QiskitError as e:
            message = e.message.rstrip("\n .")
            message = e.message.rstrip(".'")
            if message.endswith("Error code: 3458"):
                print_stderr("You don't have enough credits to run this job.")
                return {"result": ThinPromise(lambda: None), "transpiled_circuit": None}

            raise


class IBMJob(VendorJob):
    def __init__(self):
        super().__init__()
        self.circuit = None

    @abstractmethod
    def run(self, device):
        device = device.device
        self.device_info = {}
        cfg = device.configuration()
        if cfg is not None:
            self.device_info["configuration"] = cfg.to_dict()
        prop = device.properties()
        if prop is not None:
            self.device_info["properties"] = prop.to_dict()

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
        if device.configuration().coupling_map is None:
            return None

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
        assert len(providers) > 0, "no account loaded"

        # choose account with most backends coming up last
        providers.sort(key=lambda p: len(p.backends()))

        self.IBMQ_cloud_providers = providers

        print_hl("IBMQ cloud account loaded.")

    @functools.lru_cache()
    def get_devices(self):
        devices = {}
        for provider in self.IBMQ_cloud_providers:
            devices.update(
                {device.name(): IBMDevice(device) for device in provider.backends()}
            )
        return devices


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
