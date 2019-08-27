from qiskit import IBMQ, execute
# from qiskit.providers.models.jobstatus import JobStatus
import pickle
import time

# This class will manage the jobs that are being sent to the IBM devices during one particular experiment.
# It can store the progress in a file such that one can retrieve the status of the experiment at a later point in time (i.e., several days).
# Do make sure that you have set up your IBM account on your local device before using this job manager.
class JobManager:

    # One can construct a job manager with the following arguments:
    # - String Name: the name of the experiment. This will determine the file name in which the progress is stored.
    # - Obj Params: an object containing the parameters that were used in devising the experiment.
    # - Obj results: an object where the results are to be stored.
    # - Fn print_result_function: a function that will display the final results of the experiment.
    def __init__(self, name, params = None, results = None, print_result_function = None):
        self.name = name
        self.params = params if params is not None else {}
        self.results = results
        self.print_result_function = print_result_function
        self.jobs = []
        self.pending_jobs = {}
        self.received_jobs = {}
        self._provider = None

    @property
    def provider(self):
        if self._provider is None:
            self._provider = IBMQ.load_account()
        return self._provider

    # This will print a progress message, indicating how the experiment is progressing
    def print_status(self):
        print("Current timestamp:", time.ctime())
        print("Number of jobs queued:", len(self.jobs))
        print("Number of jobs pending:", len(self.pending_jobs))
        if self.pending_jobs: print("Job IDs:", ', '.join(self.pending_jobs.keys()))
        print("Number of jobs finished:", len(self.received_jobs))
        if self.received_jobs: print("Job IDs:", ', '.join(self.received_jobs.keys()))

    # This will call the function that displays the final result
    def print_result(self):
        if self.print_result_function is not None:
            print("The final results function is now being run...")
            self.print_result_function(self.results, self.params)
            print("Done.")

    # This function will determine whether the experiment is finished
    def is_finished(self):
        if self.pending_jobs or self.jobs:
            return False
        return True

    # With this function, one can add a new job to the experiment.
    # The arguments are:
    # - QuantumCircuit circuit: a qiskit QuantumCircuit object that contains the circuit that is to be run.
    # - String backend_name: this is the name of the backend device on which the circuit is to be run.
    # - Fn callback: this is the function that is to be run once the results are in.
    # - Iter args: this is a container of all the arguments that are to be passed to the callback function, once the results are in.
    # - Int shots: this is the number of runs that are to be executed by IBM.
    # - Int max_credits: this is the maximum number of credits one wants to spend on this circuit.
    def add_job(self, circuit, backend_name, callback, args, shots = 1024, max_credits = 0):
        self.jobs.append((circuit, backend_name, callback, args, shots, max_credits))

    # This function will attempt to send all the jobs over to IBM
    def send_jobs(self):
        todel = set()
        backends = {}
        for i, (circuit, backend_name, callback, args, shots, max_credits) in enumerate(self.jobs):

            # Print what is to be sent
            print("Sending job {}/{}.".format(i+1, len(self.jobs)))
            print("Circuit:")
            print(circuit)

            # Provide the necessary delay to not spam the IBM server too much
            time.sleep(.5)

            # Getting the backend
            try:
                if backend_name in backends:
                    backend = backends[backend_name]
                else:
                    backend = self.provider.get_backend(backend_name)
                    backends[backend_name] = backend
            except Exception as e:
                print("An error occured getting the backend.")
                raise

            # Executing the job
            try:
                job = execute(circuit, backend, shots = shots, max_credits = max_credits)
            except Exception as e:
                print("An error occured executing the job.")
                raise

            # Getting the job ID
            try:
                job_id = job.job_id()
            except Exception as e:
                print("An error occurred obtaining the job id of the job.")
                if e.message.rstrip('\n').rstrip(' ').rstrip('.').endswith('QUEUE_DISABLED'):
                    print("The queue for this backend is disabled.")
                    print("This probably means it is under maintenance.")
                    print("Try to run the update script at a later stage.")
                    break
                elif e.message.rstrip('\n').rstrip(' ').rstrip('.').endswith('NOT_CREDITS_AVALIABLES'):
                    print("You don't have enough credits to run this job.")
                    print("That is why we will suspend sending any further jobs for now.")
                    print("Try to run the update script at a later stage.")
                    break
                else:
                    raise
            print("Job ID:", job_id)

            # Modify the data structures
            self.pending_jobs[job_id] = (circuit, backend_name, callback, args)
            todel.add(i)

            # Print completion message
            print("Done.")

        # Remove the sent jobs
        for i in sorted(todel, reverse = True):
            del self.jobs[i]

    # This function will obtain and parse the results of a particular job_id
    def parse_results(self, job_id, circuit, backend_name, callback, args):

        # Contact IBM to get information about the job
        try:
            backend = self.provider.get_backend(backend_name)
            job = backend.retrieve_job(job_id)
        except Exception as e:
            print("An error occurred retrieving the job with job id:", job_id)
            print(repr(e))
            return "RETRIEVE ERROR"

        # Get the status of the job
        status = job.status()._name_
        if job.status()._name_ != "DONE":
            print("Status:", status)
            return status

        # If the job is done, try to get the results
        try:
            result = job.result()
        except Exception as e:
            print("An error occurred retrieving the results of the job with job id:", job_id)
            print(repr(e))
            return "RESULT ERROR"

        # Parse the results
        try:
            self.results = callback(circuit, result, self.results, self.params, *args)
        except Exception as e:
            print("An error occurred executing the callback of the job with job id:", job_id)
            print(repr(e))
            return "PARSE ERROR"

        # Notify the caller function that the job was closed successfully
        return "DONE"

    # This function will check whether there are new results to be processed
    def check_pending_jobs(self):
        todel = set()
        for i, (job_id, (circuit, backend_name, callback, args)) in enumerate(self.pending_jobs.items()):
            time.sleep(.5)
            print("Attempting to retrieve job {}/{} with job id {}.".format(i+1, len(self.pending_jobs), job_id))
            status = self.parse_results(job_id, circuit, backend_name, callback, args)
            if status == "DONE":
                print("This job finished successfully. Job ID:", job_id)
                todel.add(job_id)
                self.received_jobs[job_id] = (status, circuit, backend_name, callback, args)
            elif status == "ERROR":
                print("This job has finished with an error, so its results are treated as a missing value.")
                print("Job ID:", job_id)
                print("Circuit:")
                print(circuit)
                print("Arguments:", args)
                todel.add(job_id)
                self.received_jobs[job_id] = (status, circuit, backend_name, callback, args)
            elif status == "RUNNING":
                print("This job is still running.")
            elif status == "QUEUED":
                print("This job is queued.")
            elif status == "RETRIEVE ERROR":
                print("This job could currently not be retrieved.")
            elif status == "RESULT ERROR":
                print("The results of this job could currently not be retrieved.")
            elif status == "PARSE ERROR":
                print("The results of this job could not be parsed. The job is therefore cancelled.")
                print("Job ID:", job_id)
                print("Circuit:")
                print(circuit)
                print("Arguments:", args)
                todel.add(job_id)
                self.received_jobs[job_id] = (status, circuit, backend_name, callback, args)
            else:
                print("This job returned an unknown status:", status)
                print("The next update will attempt to obtain the status of this job again.")
        for job_id in todel:
            del self.pending_jobs[job_id]

    # This function will recalculate the results from the measurement outcomes of the already received jobs
    def reparse_results(self):
        for i, (job_id, (status, circuit, backend_name, callback, args)) in enumerate(self.received_jobs.items()):
            print("Attempting to reparse the results of job {}/{} with job id {}.".format(i+1, len(self.received_jobs), job_id))
            if status != "DONE": continue
            time.sleep(.5)
            self.parse_results(job_id, circuit, backend_name, callback, args)

    # This function will retry all jobs that failed with an error
    def retry_failed_jobs(self):
        todel = set()
        for job_id, (status, circuit, backend_name, callback, args) in self.received_jobs.items():
            if status != "DONE":
                print("The status of the job with JobID {} was:".format(job_id), status)
                if status == "PARSE ERROR":
                    print("As the status was PARSE ERROR, we will not try to run it again, as it will fail again.")
                    print("Please make a new job where you fix the parsing code.")
                else:
                    self.add_job(circuit, backend_name, callback, args)
                    todel.add(job_id)
        for job_id in todel:
            del self.received_jobs[job_id]

    # This function can be used to update the experiments progress
    def default_update(self):
        self.load_from_file()
        self.print_status()
        self.send_jobs()
        self.save_to_file()
        self.retry_failed_jobs()
        self.save_to_file()
        self.check_pending_jobs()
        self.save_to_file()
        self.print_result()
        return self.is_finished()

    # This function will load an experiment from a file
    def load_from_file(self):
        print("Loading job manager from file...")
        with open('experiments/{}.pkl'.format(self.name), 'rb') as f:
            self.params, self.results, self.print_result_function, self.jobs, self.pending_jobs, self.received_jobs = pickle.load(f)
        print("Done.")

    # This function saves the progress of the experiment in a file
    def save_to_file(self):
        print("Saving job manager to file...")
        with open('experiments/{}.pkl'.format(self.name), 'wb') as f:
            pickle.dump((self.params, self.results, self.print_result_function, self.jobs, self.pending_jobs, self.received_jobs), f)
        print("Done.")
