from abc import ABC, abstractmethod

import braket, braket.circuits


class AmazonPromiseBase(ABC):
    """
    Thin wrapper about local promise class.
    Thick wrapper around cloud promise class.
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

    @abstractmethod
    def freeze(self):
        pass

    @abstractmethod
    def thaw(self):
        pass


class AmazonCloudPromise(AmazonPromiseBase):
    """
    Do not use - we don't know what the interface looks like yet
    """

    def __init__(self):
        raise NotImplementedError()


class AmazonMeasureLocalPromise(AmazonPromiseBase):
    """
    Thin wrapper about LocalQuantumTask
    """

    def __init__(self, circuit: braket.circuits.Circuit, device, num_shots: int):
        super().__init__()

        self.task = device.run(circuit, shots=num_shots)

    def job_id(self):
        """
        Return a job id.
        Will have to be updated to match the Google API at some point.
        """
        return self.task.id

    def status(self):
        """
        Return the status.
        """
        return "DONE" if self.task.state() == "COMPLETED" else "FAILURE"

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

    def result(self):
        return self.task.result()