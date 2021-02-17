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
    AWS Cloud Promise
    """

    def __init__(
        self,
        circuit: braket.circuits.Circuit,
        device,
        num_shots: int,
        *,
        s3_bucket: str = "quantum-bench",
        s3_bucket_folder: str = ""
    ):
        super().__init__()

        self.s3_path = (s3_bucket, s3_bucket_folder)
        self.task = device.run(circuit, self.s3_path, shots=num_shots, poll_timeout_seconds=5*24*60*60)

    def job_id(self):
        """
        Return a job id.
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
        self.task = self.job_id()
        return self

    def thaw(self):
        """
        No thawing necessary.
        The real promise should probably have this method in the frozen instance class.
        """
        self.task = braket.aws.AwsQuantumTask(arn=self.task)
        return self

    def result(self):
        return self.task.result()


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
