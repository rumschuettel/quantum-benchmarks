from abc import ABC, abstractmethod
import cirq


class GooglePromiseBase(ABC):
    """
        As the simulators in cirq do not return any promise, we write our own
        promise class. This should be a very thin wrapper around the existing
        promise structure provided by google which we conjecture to exist.
    """

    @abstractmethod
    def job_id(self):
        raise NotImplementedError()

    @abstractmethod
    def status(self):
        raise NotImplementedError()

    @abstractmethod
    def result(self):
        raise NotImplementedError()


class GooglePromise(GooglePromiseBase):
    def __init__(self, circuit: cirq.Circuit, device, repetitions: int):
        raise NotImplementedError("The google api to their hardware is not available yet.")

    def job_id(self):
        raise NotImplementedError()

    def status(self):
        raise NotImplementedError()

    def result(self):
        raise NotImplementedError()

    def freeze(self):
        raise NotImplementedError()

    def thaw(self):
        raise NotImplementedError()


class GoogleLocalPromise(GooglePromiseBase):
    """
        As the simulators in cirq do not return any promise, but just return
        the result directly, we emulate this behavior here.
    """

    def __init__(
        self, circuit: cirq.Circuit, device, repetitions: int, simulate: bool, *args, **kwargs
    ):
        super().__init__()

        self.device = device
        self.circuit = circuit
        self.repetitions = repetitions
        self.simulate = simulate
        self._result = None

    def job_id(self):
        """
            Return a job id.
            Will have to be updated to match the Google API at some point.
        """
        return id(self)

    def status(self):
        """
            Return the status.
            Will have to be updated to match the Google API at some point.
        """
        return "PENDING" if self._result is None else "DONE"

    def result(self):
        """
            Run the simulator if results are requested.
        """
        if self._result is None:
            if self.simulate:
                self._result = self.device.simulate(self.circuit)
            else:
                self._result = self.device.run(self.circuit, repetitions=self.repetitions)
        return self._result

    def freeze(self):
        """
            Since promises that resolve immediately will never be pickled, we can just pass self.
            The real promise can return a separate frozen instance if necessary.
        """
        return self

    def thaw(self):
        """
            No thawing necessary.
            The real promise should probably have this method in the frozen instance class.
        """
        return self
