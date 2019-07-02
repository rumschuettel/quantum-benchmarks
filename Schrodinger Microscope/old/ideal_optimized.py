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

# Build the circuit
qubits = [cirq.GridQubit(0,i) for i in range(2**num_post_selections)]
circuit = cirq.Circuit()
for i in range(num_post_selections):
    for x in range(0,2**num_post_selections,2**(i+1)):
        circuit.append(cirq.CNOT(qubits[x], qubits[x + 2**i]))
        circuit.append([cirq.S(qubits[x]), cirq.H(qubits[x]), cirq.S(qubits[x])])

# Print the circuit
print("The circuit that is being used for benchmarking is:")
print()
print(circuit_to_string(circuit))
print()

# Loop over the pixels
xs = np.linspace(-2,2,num_pixels+1)
xs = .5*(xs[:-1] + xs[1:])
ys = np.linspace(-2,2,num_pixels+1)
ys = .5*(ys[:-1] + ys[1:])
psps = np.empty((len(xs),len(ys)), dtype = np.float64)
zs = np.empty((len(xs),len(ys)), dtype = np.float64)
for (i,x),(j,y) in it.product(enumerate(xs),enumerate(ys)):
    z = x + 1j*y

    # Set up the initial state
    psi = np.array([z,1], dtype = np.complex64) / np.sqrt(x**2 + y**2 + 1)
    init_state = reduce(lambda x,y : np.kron(x,y), [psi]*(2**num_post_selections))

    # Run the simulation
    res = cirq.Simulator().simulate(circuit, initial_state = np.array(init_state), qubit_order = qubits)

    # Calculate the measurement probabilities from the final state
    psp = np.linalg.norm(res.final_state[::2**(2**num_post_selections-1)])**2
    sp = np.abs(res.final_state[2**(2**num_post_selections-1)])**2 / psp if psp > 0 else 0

    # Simulate the measurements
    num_post_selected = np.random.binomial(num_runs,psp)
    psps[j,i] = num_post_selected / num_runs
    zs[j,i] = np.random.binomial(num_post_selected,sp) / num_post_selected if num_post_selected > 0 else 0

    # Print the progress
    print("Progress: {:.3f}%".format(100*(i*num_pixels+j+1)/num_pixels**2), end = '\r')
print()

# Display some statistics
print("Simulated average post selection probability: {:.3f}%".format(100*np.mean(np.array(psps).flatten())))
print("Simulated average success probability: {:.3f}%".format(100*np.mean(np.array(zs).flatten())))

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
