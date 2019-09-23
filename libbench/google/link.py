from libbench.lib import print_hl
from libbench.link import VendorLink, VendorJob
import cirq

# Support for the density matrix simulator can be added later if necessary.
# For now does not seem to be worth the time.

GOOGLE_LOCAL_DEVICES = (
    cirq.Simulator,
    # cirq.DensityMatrixSimulator
)

GOOGLE_DEVICES = {
    'sparse_simulator' : cirq.Simulator(),
    # 'density_matrix_simulator' : cirq.DensityMatrixSimulator()
}


class GoogleJob(VendorJob):
    pass


class GoogleLink(VendorLink):
    def __init__(self):
        super().__init__()

        print_hl("cirq runner loaded.")

    def get_devices(self):
        """
            Retrieves the available simulators in cirq.
            Note that cirq has no built-in method for listing the available
            simulators, so these will have to be added manually upon every update
            of cirq, or some dirty python code has to be written that checks whether
            the available classes that derive from the cirq codebase have a
            simulator signature.
        """
        return GOOGLE_DEVICES

    def run(self, job: GoogleJob):
        raise NotImplementedError()

class GoogleSimulatorLink(VendorLink):
    def __init__(self):
        super().__init__()

        print_hl("cirq simulator loaded.")

    def get_devices(self):
        """
            Retrieves the available simulators in cirq.
            Note that cirq has no built-in method for listing the available
            simulators, so these will have to be added manually upon every update
            of cirq, or some dirty python code has to be written that checks whether
            the available classes that derive from the cirq codebase have a
            simulator signature.
        """
        return GOOGLE_DEVICES

    def run(self, job: GoogleJob):
        pass
