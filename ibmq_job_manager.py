from qiskit import IBMQ, execute
from qiskit.providers.models.jobstatus import JobStatus
import pickle
import time

# ids = []
# with open('ids') as f:
#     for line in f:
#         if len(line.strip('\n')) == 0: continue
#         ids.append(line.strip('\n'))

class JobManager:
    def __init__(self, name, results = None, print_result_function = None):
        self.name = name
        self.jobs = []
        self.pending_jobs = {}
        self.received_jobs = set()
        self.results = results
        self.print_result_function = print_result_function
        self.provider = IBMQ.load_account()

    def print_status(self):
        print("Current timestamp:", time.ctime())
        print("Number of jobs queued:", len(self.jobs))
        print("Number of jobs pending:", len(self.pending_jobs))
        if self.pending_jobs: print("Job IDs:", ', '.join(self.pending_jobs.keys()))
        print("Number of jobs finished:", len(self.received_jobs))
        if self.received_jobs: print("Job IDs:", ', '.join(self.received_jobs))

    def print_result(self):
        if self.print_result_function is not None:
            print("The result is:")
            self.print_result_function(self.results)

    def add_job(self, circuit, backend_name, callback, args, shots = 1024, max_credits = 0):
        self.jobs.append((circuit, backend_name, callback, args, shots, max_credits))
        # id = ids.pop(0)
        # self.pending_jobs[id] = (circuit, backend_name, callback, args)

    def send_jobs(self):
        todel = set()
        for i,(circuit, backend_name, callback, args, shots, max_credits) in enumerate(self.jobs):
            time.sleep(1)
            try:
                print()
                print("Sending a new job.")
                print("Circuit:")
                print(circuit)
                backend = self.provider.get_backend(backend_name)
                job = execute(circuit, backend, shots = shots, max_credits = max_credits)
                job_id = job.job_id()
                self.pending_jobs[job_id] = (circuit, backend_name, callback, args)
                todel.add(i)
                print("Job ID:", job_id)
                print("Done.")
            except Exception as e:
                print("An error occurred sending a job.")
                print(repr(e))
        for i in sorted(todel, reverse = True):
            del self.jobs[i]

    def check_pending_jobs(self):
        todel = set()
        for job_id,(circuit, backend_name, callback, args) in self.pending_jobs.items():
            time.sleep(1)
            try:
                backend = self.provider.get_backend(backend_name)
                job = backend.retrieve_job(job_id)
            except Exception as e:
                print("An error occurred retrieving the job with job id:", job_id)
                print(repr(e))
                continue
            if job.status()._name_ != "DONE":
                continue
            try:
                result = job.result()
            except Exception as e:
                print("An error occurred retrieving the results of the job with job id:", job_id)
                print(repr(e))
                continue
            todel.add(job_id)
            print()
            print("New job finished. Job ID:", job_id)
            try:
                callback(circuit, result, self.results, *args)
            except Exception as e:
                print("An error occurred executing the callback of the job with job id:", job_id)
                print(repr(e))
            self.received_jobs.add(job_id)
        for job_id in todel:
            del self.pending_jobs[job_id]

    def load_from_file(self):
        with open('experiment_{}.pkl'.format(self.name), 'rb') as f:
            self.jobs, self.pending_jobs, self.received_jobs, self.results, self.print_result_function = pickle.load(f)

    def save_to_file(self):
        with open('experiment_{}.pkl'.format(self.name), 'wb') as f:
            pickle.dump((self.jobs, self.pending_jobs, self.received_jobs, self.results, self.print_result_function), f)
