import numpy as np
np.set_printoptions(linewidth=200)
import matplotlib.pyplot as plt
from qiskit import IBMQ, QuantumCircuit, execute
from job_manager import JobManager
from experiment import construct_circuits,parse_measurement_outcomes

def fill_result(circuit, exp_result, results, j, i):
    res = exp_result.get_counts(circuit)
    psp,z = parse_measurement_outcomes(res, 1, 1024)
    results[0][j][i] = psp
    results[1][j][i] = z

def draw_result(results):
    psps,zs = results

    fig = plt.figure()
    ax_psps = fig.add_subplot(1,2,1)
    ax_zs = fig.add_subplot(1,2,2)

    # Draw the post selection probabilities
    ax_psps.imshow(psps, cmap = 'gray', extent = (-2,2,-2,2), vmin = 0, vmax = 1)
    ax_psps.set_title('PSP({},{})'.format(1, 1024))
    ax_psps.set_xlabel('Re(z)')
    ax_psps.set_ylabel('Im(z)')

    # Draw the success probabilities
    ax_zs.imshow(zs, cmap = 'gray', extent = (-2,2,-2,2), vmin = 0, vmax = 1)
    ax_zs.set_title('SP({},{})'.format(1, 1024))
    ax_zs.set_xlabel('Re(z)')
    ax_zs.set_ylabel('Im(z)')

    plt.show()

def setup(name, num_post_selections, num_pixels, num_runs, xmin = -2, xmax = 2, ymin = -2, ymax = 2):
    psps = [[None]*num_pixels for _ in range(num_pixels)]
    zs = [[None]*num_pixels for _ in range(num_pixels)]
    jm = JobManager(name, (psps,zs), draw_result)
    circuits = construct_circuits(num_post_selections, num_pixels, xmin = xmin, xmax = xmax, ymin = ymin, ymax = ymax)
    for (j,i),circuit in circuits.items():
        jm.add_job(circuit, 'ibmq_qasm_simulator', fill_result, [j,i])
    jm.save_to_file()

def update(name):
    jm = JobManager(name)
    jm.load_from_file()
    jm.print_status()
    jm.send_jobs()
    jm.check_pending_jobs()
    jm.save_to_file()
    jm.print_result()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Please supply what you want to do in the command line.")
    else:
        if sys.argv[1] == 'setup':
            setup('Schrodinger2-16', 1, 16, 1024)
        elif sys.argv[1] == 'update':
            update('Schrodinger2-16')
        else:
            print("Unknown command line argument supplied.")
