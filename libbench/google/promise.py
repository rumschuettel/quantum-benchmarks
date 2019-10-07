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
        pass

    @abstractmethod
    def status(self):
        pass

    @abstractmethod
    def result(self):
        pass


class GoogleCloudPromise(GooglePromiseBase):
    """
        Do not use - we don't know what the interface looks like yet
    """
    pass


class GoogleLocalPromise(GooglePromiseBase):
    """
        As the simulators in cirq do not return any promise, but just return
        the result directly, we emulate this behavior here.
    """

    def __init__(self, circuit: cirq.Circuit, device):
        super().__init__()

        self.device = device
        self.circuit = circuit
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

    @abstractmethod
    def result(self):
        """
            Run the simulator if results are requested.
        """
        raise NotImplementedError()

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


class GoogleMeasureLocalPromise(GoogleLocalPromise):
    def __init__(self, *args, num_shots: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.num_shots = num_shots

    def result(self):
        if self._result is None:
            self._result = self.device.run(self.circuit, repetitions=self.num_shots)
        return self._result

class GoogleStatevectorPromise(GoogleLocalPromise):
    def __init__(self, *args, num_shots: int, **kwargs):
        super().__init__(*args, **kwargs)

    def result(self):
        if self._result is None:
            self._result = self.device.simulate(self.circuit)
        return self._result
