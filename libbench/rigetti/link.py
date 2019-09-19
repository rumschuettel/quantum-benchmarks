import pyquil as pq

class RigettiLink:
    @staticmethod
    def list_devices():
        print(pq.list_quantum_computers())

    @staticmethod
    def test():
        from pyquil.gates import CNOT, Z
        # to run on real device, change as_qvm=False
        qvm = pq.get_qc('9q-square', as_qvm=True)
        prog = pq.Program(Z(0), CNOT(0, 1))

        results = qvm.run_and_measure(prog, trials=10)
        print(results)
