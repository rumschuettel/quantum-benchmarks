import numpy as np
np.set_printoptions(linewidth=200)
import cirq
import matplotlib.pyplot as plt
import itertools as it
from functools import reduce

def circuit_to_string(circuit):
    if len(circuit._moments) == 0:
        return "  << This circuit is empty >>"
    return "  " + str(circuit).replace('\n','\n  ')

# Set the number of iterations
num_post_selections = 2
num_pixels = 64
num_runs = 1024

# Loop over the pixels
xs = np.linspace(-2,2,num_pixels+1)
xs = .5*(xs[:-1] + xs[1:])
ys = np.linspace(-2,2,num_pixels+1)
ys = .5*(ys[:-1] + ys[1:])
zs = np.empty((len(xs),len(ys)), dtype = np.float64)
psps = np.empty((len(xs),len(ys)), dtype = np.float64)
for (i,x),(j,y) in it.product(enumerate(xs),enumerate(ys)):
    z = x + 1j*y

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
    circuit.append(cirq.measure(*(qubits[k] for k in range(1,2**num_post_selections)), key = 'post_selection'))
    circuit.append(cirq.measure(qubits[0], key = 'success'))

    # Run the simulator
    res = cirq.Simulator().run(circuit, repetitions = num_runs)

    # Find the measurement outcome statistics
    post_selection_result = list(not any(outcome) for outcome in res.measurements['post_selection'])
    num_post_selected = post_selection_result.count(True)
    psps[j,i] = num_post_selected / num_runs
    zs[j,i] = list(success and post_selected for success,post_selected in zip(res.measurements['success'], post_selection_result)).count(True) / num_post_selected if num_post_selected > 0 else 0

    # Print the progress
    print("Progress: {:.3f}%".format(100*(i*num_pixels+j+1)/num_pixels**2), end = '\r')
print()

# Display some statistics
print("Average post-selection probability: {:.3f}%".format(100*np.mean(np.array(psps).flatten())))
print("Average success probability: {:.3f}%".format(100*np.mean(np.array(zs).flatten())))

# Plot the resulting figure based on the measurement statistics
fig = plt.figure(figsize = (12,6))
ax = fig.add_subplot(1,2,1)
ax.imshow(psps, cmap = 'gray', extent = (-2,2,-2,2), vmin = 0, vmax = 1)
ax.set_title('Post selection probability')
ax.set_xlabel('Re(z)')
ax.set_ylabel('Im(z)')
ax = fig.add_subplot(1,2,2)
ax.imshow(zs, cmap = 'gray', extent = (-2,2,-2,2), vmin = 0, vmax = 1)
ax.set_title('Success probability')
ax.set_xlabel('Re(z)')
ax.set_ylabel('Im(z)')
plt.show()
