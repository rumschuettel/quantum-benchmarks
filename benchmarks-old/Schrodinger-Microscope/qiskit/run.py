import numpy as np
np.set_printoptions(linewidth=200)
import matplotlib.pyplot as plt
from qiskit import IBMQ, QuantumCircuit, execute
from job_manager import JobManager
from experiment import construct_circuits,parse_measurement_outcomes

def fill_result(circuit, exp_result, results, params, j, i):
    num_post_selections = params['num_post_selections']
    num_runs = params['num_runs']
    res = exp_result.get_counts() # circuit)
    psp,z = parse_measurement_outcomes(res, num_post_selections, num_runs)
    results[0][j][i] = psp
    results[1][j][i] = z
    return results

def draw_result(results, params):
    num_post_selections = params['num_post_selections']
    num_pixels = params['num_pixels']
    num_runs = params['num_runs']
    backend_name = params['backend_name']
    psps,zs = results

    fig = plt.figure()
    ax_psps = fig.add_subplot(1,2,1)
    ax_zs = fig.add_subplot(1,2,2)

    # Draw the post selection probabilities
    ax_psps.imshow(psps, cmap = 'gray', extent = (-2,2,-2,2), vmin = 0, vmax = 1)
    ax_psps.set_title('PSP({},{})'.format(num_post_selections, num_runs))
    ax_psps.set_xlabel('Re(z)')
    ax_psps.set_ylabel('Im(z)')

    # Draw the success probabilities
    ax_zs.imshow(zs, cmap = 'gray', extent = (-2,2,-2,2), vmin = 0, vmax = 1)
    ax_zs.set_title('SP({},{})'.format(num_post_selections, num_runs))
    ax_zs.set_xlabel('Re(z)')
    ax_zs.set_ylabel('Im(z)')

    plt.savefig('experiments/Schrodinger{}-{}-{}-{}.png'.format(num_post_selections, num_pixels, num_runs, backend_name))

def setup(name, num_post_selections, num_pixels, num_runs, backend_name):
    params = {
        'num_post_selections' : num_post_selections,
        'num_pixels' : num_pixels,
        'num_runs' : num_runs,
        'backend_name' : backend_name
    }
    psps = [[0]*num_pixels for _ in range(num_pixels)]
    zs = [[0]*num_pixels for _ in range(num_pixels)]
    jm = JobManager(name, params, (psps,zs), draw_result)
    circuits = construct_circuits(num_post_selections, num_pixels)
    for (j,i),circuit in circuits.items():
        jm.add_job(circuit, backend_name, fill_result, [j,i], shots = num_runs)
    jm.save_to_file()

def update(name):
    jm = JobManager(name)
    return jm.default_update()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Please supply what you want to do in the command line.")
        print("The first command line argument should be either:")
        print(" - setup: this is for setting up a new experiment (will overwrite existing ones!)")
        print(" - update: this is for updating a running experiment with the newest results.")
    else:
        if sys.argv[1] == 'setup':
            print("Setting up an experiment.")
            if len(sys.argv) < 7:
                print("You need to supply 5 more command line arguments:")
                print(" - The name you want to give to your experiment.")
                print(" - The number of post selection rounds you want to perform.")
                print(" - The number of pixels in every dimension you want.")
                print(" - The number of runs you want to perform per pixel.")
                print(" - The name of the backend you would like to use.")
            else:
                name = sys.argv[2]
                num_post_selections = int(sys.argv[3])
                num_pixels = int(sys.argv[4])
                num_runs = int(sys.argv[5])
                backend_name = sys.argv[6]
                print("Parameters:")
                print(" - Number of rounds of post selection:", num_post_selections)
                print(" - Number of pixels:", num_pixels)
                print(" - Number of runs:", num_runs)
                print(" - Backend name:", backend_name)
                print("Are you sure you want to set up this experiment?")
                print("It would involve {} calls to {}.".format(num_pixels**2, backend_name))
                answer = input("yes/no: ")
                if answer != 'yes':
                    print("Aborting.")
                    sys.exit()
                setup('Schrodinger{}-{}-{}-{}'.format(num_post_selections, num_pixels, num_runs, backend_name), num_post_selections, num_pixels, num_runs, backend_name)
        elif sys.argv[1] == 'update':
            print("Updating an experiment.")
            if len(sys.argv) < 3:
                print("You need to supply the name of the experiment you want to update.")
            else:
                name = sys.argv[2]
                print("Updating experiment with name:", name)
                result = update(name)
                sys.exit(0 if result else 1)
        else:
            print("Unknown command line argument, {}, supplied.".format(sys.argv[1]))
