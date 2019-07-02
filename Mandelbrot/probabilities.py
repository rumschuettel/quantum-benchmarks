import numpy as np
np.set_printoptions(linewidth=200)
import matplotlib.pyplot as plt
import itertools as it
from functools import reduce
import cirq

def circuit_to_string(circuit):
    if len(circuit._moments) == 0:
        return "  << This circuit is empty >>"
    return "  " + str(circuit).replace('\n','\n  ')

# Set the parameters
num_post_selections = 2
num_pixels = 64

# Set up the grid
xs = np.linspace(-2.5,2.5,num_pixels+1)
xs = .5*(xs[:-1] + xs[1:])
ys = np.linspace(-2.5,2.5,num_pixels+1)
ys = .5*(ys[:-1] + ys[1:])
zs = np.empty((len(xs),len(ys)), dtype = np.float64)
psps = np.empty((len(xs),len(ys)), dtype = np.float64)
for (i,x),(j,y) in it.product(enumerate(xs),enumerate(ys)):
    c = x + 1j*y

    # Calculate the required circuit parameters
    r2 = abs(c) * np.sqrt(1 + .5*np.sqrt(1 + 4/abs(c)**2))
    r1 = 1/r2
    phi = np.angle(c)
    r1rot = -2*np.arccos(1/np.sqrt(1.+r1**2))
    r2rot = -2*np.arccos(1/np.sqrt(1.+r2**2))

    # Set up the circuit
    qubits = [cirq.GridQubit(0,i) for i in range(2**num_post_selections)]
    circuit = cirq.Circuit()
    for k in range(2**num_post_selections):
        circuit.append(cirq.X(qubits[k]))
    for k in range(1,num_post_selections+1):
        for l in range(0,2**num_post_selections,2**k):
            circuit.append(cirq.CNOT(qubits[l],qubits[l+2**(k-1)]))
            circuit.append(cirq.H(qubits[l]).controlled_by(qubits[l+2**(k-1)]))
            circuit.append(cirq.Ry(r1rot)(qubits[l+2**(k-1)]).controlled_by(qubits[l]))
            circuit.append(cirq.CZ(qubits[l],qubits[l+2**(k-1)]))
            circuit.append(cirq.Rz(phi)(qubits[l]))
            circuit.append(cirq.Rz(-phi)(qubits[l+2**(k-1)]))
            circuit.append(cirq.X(qubits[l+2**(k-1)]))
            circuit.append(cirq.Ry(r2rot)(qubits[l]).controlled_by(qubits[l+2**(k-1)]))
            circuit.append(cirq.CZ(qubits[l],qubits[l+2**(k-1)]))
            circuit.append(cirq.CNOT(qubits[l],qubits[l+2**(k-1)]))
            circuit.append(cirq.X(qubits[l+2**(k-1)]))

    # Run the simulation
    res = cirq.Simulator().simulate(circuit, qubit_order = qubits)

    # Extract the resulting probabilities from the final state
    psps[j,i] = np.linalg.norm(res.final_state[::2**(2**num_post_selections-1)])**2
    zs[j,i] = np.abs(res.final_state[2**(2**num_post_selections-1)])**2 / psps[j,i] if psps[j,i] > 0 else 0
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
