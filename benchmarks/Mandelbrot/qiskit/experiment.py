import numpy as np
np.set_printoptions(linewidth=200)
from qiskit import QuantumCircuit, execute, Aer
from qiskit.providers.aer import StatevectorSimulator
import matplotlib.pyplot as plt
import itertools as it
from functools import reduce

def circuit_to_string(circuit):
    # Display the circuit
    return "\n  " + str(circuit).replace('\n','\n  ') + "\n"

def construct_circuit(num_post_selections, c, add_measurements = True):
    # Calculate the required circuit parameters
    r2 = abs(c) * np.sqrt(1 + .5*np.sqrt(1 + 4/abs(c)**2))
    r1 = 1/r2
    phi = np.angle(c)
    r1rot = -2*np.arccos(1/np.sqrt(1.+r1**2))
    r2rot = -2*np.arccos(1/np.sqrt(1.+r2**2))

    # Set up the circuit
    circuit = QuantumCircuit(2**num_post_selections, 2**num_post_selections) if add_measurements else QuantumCircuit(2**num_post_selections)
    for k in range(2**num_post_selections):
        circuit.x(k)
    for k in range(1,num_post_selections+1):
        for l in range(0,2**num_post_selections,2**k):
            circuit.cx(l, l+2**(k-1))
            circuit.ch(l+2**(k-1), l)
            circuit.cu3(r1rot, 0, 0, l, l+2**(k-1)) # cu3(theta,0,0) == cry(theta)
            circuit.cz(l, l+2**(k-1))
            circuit.rz(phi, l)
            circuit.rz(-phi, l+2**(k-1))
            circuit.x(l+2**(k-1))
            circuit.cu3(r2rot, 0, 0, l+2**(k-1), l)
            circuit.cz(l, l+2**(k-1))
            circuit.cx(l, l+2**(k-1))
            circuit.x(l+2**(k-1))
    if add_measurements:
        circuit.measure(list(range(2**num_post_selections)), list(range(2**num_post_selections)))

    # Return the resulting circuit
    return circuit

def simulate_mandelbrot(num_post_selections, num_pixels, num_runs = float("Inf"), xmin = -2.5, xmax = 2.5, ymin = -2.5, ymax = 2.5, output = True):
    if output:
        print("Simulating Mandelbrot with the following parameters:")
        print(" - Number of post selection rounds:", num_post_selections)
        print(" - Number of pixels in one direction:", num_pixels)
        if num_runs == float("Inf"):
            print(" - Calculate the probabilities for each pixel exactly.")
        else:
            print(" - Number of runs per pixel:", num_runs)

    # Set up the grid
    xs = np.linspace(-2.5,2.5,num_pixels+1)
    xs = .5*(xs[:-1] + xs[1:])
    ys = np.linspace(-2.5,2.5,num_pixels+1)
    ys = .5*(ys[:-1] + ys[1:])
    zs = np.empty((len(xs),len(ys)), dtype = np.float64)
    psps = np.empty((len(xs),len(ys)), dtype = np.float64)
    for (i,x),(j,y) in it.product(enumerate(xs),enumerate(ys)):
        c = x + 1j*y

        if num_runs == float("Inf"):
            # Build the circuit
            circuit = construct_circuit(num_post_selections, c, add_measurements = False)

            # Run the simulator
            res = execute(circuit, Aer.get_backend('statevector_simulator')).result().get_statevector(circuit)

            # Calculate the probabilities from the final state
            psps[j,i] = np.linalg.norm(res[:2])**2
            zs[j,i] = np.abs(res[1])**2 / psps[j,i] if psps[j,i] > 0 else 0
        else:
            # Build the circuit
            circuit = construct_circuit(num_post_selections, c)

            # Run the simulator
            res = execute(circuit, Aer.get_backend('qasm_simulator'), shots = num_runs).result().get_counts()

            # Find the measurement outcome statistics
            failure_post_process_key = '0'*(2**num_post_selections-1) + '0'
            success_post_process_key = '0'*(2**num_post_selections-1) + '1'
            num_post_selected_failures = res[failure_post_process_key] if failure_post_process_key in res else 0
            num_post_selected_successes = res[success_post_process_key] if success_post_process_key in res else 0
            num_post_selected = num_post_selected_failures + num_post_selected_successes
            psps[j,i] = num_post_selected / num_runs
            zs[j,i] = num_post_selected_successes / num_post_selected if num_post_selected > 0 else 0

        # Print the progress
        if output: print("Progress: {:.3f}%".format(100*(i*num_pixels+j+1)/num_pixels**2), end = '\r')
    if output: print()

    if output:
        # Display some statistics
        print("Average post-selection probability: {:.3f}%".format(100*np.mean(np.array(psps).flatten())))
        print("Average success probability: {:.3f}%".format(100*np.mean(np.array(zs).flatten())))

    # Return the resulting measurement outcome statistics
    return psps, zs

def draw_simulation_results(ax_psps, ax_zs, psps, zs, num_post_selections, num_runs, xmin = -2.5, xmax = 2.5, ymin = -2.5, ymax = 2.5):
    # Draw the post selection probabilities
    ax_psps.imshow(psps, cmap = 'gray', extent = (xmin,xmax,ymin,ymax), vmin = 0, vmax = 1)
    ax_psps.set_title('PSP({},{})'.format(num_post_selections, num_runs))
    ax_psps.set_xlabel('Re(z)')
    ax_psps.set_ylabel('Im(z)')

    # Draw the success probabilities
    ax_zs.imshow(zs, cmap = 'gray', extent = (xmin,xmax,ymin,ymax), vmin = 0, vmax = 1)
    ax_zs.set_title('SP({},{})'.format(num_post_selections, num_runs))
    ax_zs.set_xlabel('Re(z)')
    ax_zs.set_ylabel('Im(z)')

def run_experiment_fill_axes(ax_psps, ax_zs, num_post_selections, num_pixels, num_runs = float("Inf"), **kwargs):
    # Perform the simulation
    psps,zs = simulate_mandelbrot(num_post_selections, num_pixels, num_runs, **kwargs)

    # Fill the axes with the simulation results
    draw_simulation_results(ax_psps, ax_zs, psps, zs, num_post_selections, num_runs, **kwargs)

if __name__ == "__main__":
    fig = plt.figure(figsize = (12,6))
    ax_psps = fig.add_subplot(1,2,1)
    ax_zs = fig.add_subplot(1,2,2)
    run_experiment_fill_axes(ax_psps, ax_zs, 2, 32, 1024)
    plt.show()
