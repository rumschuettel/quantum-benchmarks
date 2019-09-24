from abc import ABC, abstractmethod
import pyquil as pq


class RigettiPromiseBase(ABC):
    """
        As the QVM runners do not return any promise, we write our own
        promise class. This should be a very thin wrapper around the existing
        promise structure provided by Rigetti which we conjecture to exist.
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


class RigettiPromise(RigettiPromiseBase):
    def __init__(self, program: pq.Program, device: pq.api.QPU):
        raise NotImplementedError("The Rigetti api to their hardware is not available yet.")

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


class RigettiLocalPromise(RigettiPromiseBase):
    """
        As the simulators in pyquil do not return any promise, but just return
        the result directly, we emulate this behavior here.

        TODO: add pq.WavefunctionSimulator
    """

    def __init__(
        self, program: pq.Program, device: pq.api.QVM, *args, **kwargs
    ):
        super().__init__()

        self.device = device
        self.program = program
        self.args = args
        self.kwargs = kwargs
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
            self._result = self.device.run_and_measure(self.program, *self.args, **self.kwargs)
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
