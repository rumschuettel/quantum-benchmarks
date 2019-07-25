import numpy as np
np.set_printoptions(linewidth=200)
import cirq
import matplotlib.pyplot as plt
import itertools as it
from functools import reduce

def circuit_to_string(circuit):
    # Display the circuit
    if len(circuit._moments) == 0:
        return "  << This circuit is empty >>"
    return "\n  " + str(circuit).replace('\n','\n  ') + "\n"

def construct_circuit(num_post_selections, z, add_measurements = True):
    # Calculate some parameters
    theta = 2 * np.arccos(abs(z) / np.sqrt(1 + abs(z)**2))
    phi = np.angle(z)

    # Build the circuit
    qubits = [cirq.GridQubit(0,i) for i in range(2**num_post_selections)]
    circuit = cirq.Circuit()
    for k in range(2**num_post_selections):
        circuit.append(cirq.Ry(theta)(qubits[k]))
        circuit.append(cirq.Rz(-phi)(qubits[k]))
    for k in range(num_post_selections):
        for l in range(0,2**num_post_selections,2**(k+1)):
            circuit.append(cirq.CNOT(qubits[l], qubits[l + 2**k]))
            circuit.append([cirq.S(qubits[l]), cirq.H(qubits[l]), cirq.S(qubits[l])])
    if add_measurements:
        circuit.append(cirq.measure(*(qubits[k] for k in range(1,2**num_post_selections)), key = 'post_selection'))
        circuit.append(cirq.measure(qubits[0], key = 'success'))

    # Return the resulting circuit
    return circuit

def simulate_schrodinger_microscope(num_post_selections, num_pixels, num_runs = float("Inf"), xmin = -2, xmax = 2, ymin = -2, ymax = 2, output = True):
    if output:
        print("Simulating Schrödingers microscope with the following parameters:")
        print(" - Number of post selection rounds:", num_post_selections)
        print(" - Number of pixels in one direction:", num_pixels)
        if num_runs == float("Inf"):
            print(" - Calculate the probabilities for each pixel exactly.")
        else:
            print(" - Number of runs per pixel:", num_runs)

    # Loop over the pixels
    xs = np.linspace(xmin,xmax,num_pixels+1)
    xs = .5*(xs[:-1] + xs[1:])
    ys = np.linspace(ymin,ymax,num_pixels+1)
    ys = .5*(ys[:-1] + ys[1:])
    zs = np.empty((len(xs),len(ys)), dtype = np.float64)
    psps = np.empty((len(xs),len(ys)), dtype = np.float64)
    for (i,x),(j,y) in it.product(enumerate(xs),enumerate(ys)):
        z = x + 1j*y

        if num_runs == float("Inf"):
            # Build the circuit
            circuit = construct_circuit(num_post_selections, z, add_measurements = False)

            # Run the simulator
            res = cirq.Simulator().simulate(circuit)

            # Calculate the probabilities from the final state
            psps[j,i] = np.linalg.norm(res.final_state[::2**(2**num_post_selections-1)])**2
            zs[j,i] = np.abs(res.final_state[2**(2**num_post_selections-1)])**2 / psps[j,i] if psps[j,i] > 0 else 0
        else:
            # Build the circuit
            circuit = construct_circuit(num_post_selections, z)

            # Run the simulator
            res = cirq.Simulator().run(circuit, repetitions = num_runs)

            # Find the measurement outcome statistics
            post_selection_result = list(not any(outcome) for outcome in res.measurements['post_selection'])
            num_post_selected = post_selection_result.count(True)
            psps[j,i] = num_post_selected / num_runs
            zs[j,i] = list(success and post_selected for success,post_selected in zip(res.measurements['success'], post_selection_result)).count(True) / num_post_selected if num_post_selected > 0 else 0

        # Print the progress
        if output: print("Progress: {:.3f}%".format(100*(i*num_pixels+j+1)/num_pixels**2), end = '\r')
    if output: print()

    if output:
        # Display some statistics
        print("Average post-selection probability: {:.3f}%".format(100*np.mean(np.array(psps).flatten())))
        print("Average success probability: {:.3f}%".format(100*np.mean(np.array(zs).flatten())))

    # Return the aggregated measurement outcome statistics
    return psps,zs

def draw_simulation_results(ax_psps, ax_zs, psps, zs, num_post_selections, num_runs, xmin = -2, xmax = 2, ymin = -2, ymax = 2):
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

def run_experiment_fill_axes(ax_psps, ax_zs, num_post_selections, num_pixels, num_runs, **kwargs):
    # Perform the simulation
    psps,zs = simulate_schrodinger_microscope(num_post_selections, num_pixels, num_runs, **kwargs)

    # Fill the axes with the simulation results
    draw_simulation_results(ax_psps, ax_zs, psps, zs, num_post_selections, num_runs, **kwargs)

if __name__ == "__main__":
    fig = plt.figure(figsize = (12,6))
    ax_psps = fig.add_subplot(1,2,1)
    ax_zs = fig.add_subplot(1,2,2)
    run_experiment_fill_axes(ax_psps, ax_zs, 1, 64, float("Inf"))
    plt.show()
