# Schrödinger Microscope

The Schrödinger microscope is an experiment that generates a fractal.

## Parameters of the experiment

There are three parameters that any experimentalist will have to pick:

  * `p`: the number of pixels to be displayed in the final image.
  * `n`: the number of post-selection steps that are to be implemented.
  * `N`: the number of runs that an experimentalist performs to get sufficient statistics to determine the color of one pixel.

## Description

One partitions the interval `[-2,2]` into `p` bins of equal sizes, and denotes the centers of the resulting bins by `a(1), ..., a(p)`. Next, one runs the following procedure for all `z = a(j) + ia(k)`, where `j` and `k` run from `1` to `p`.

Consider the following circuit:

Circuit figure to be added.

One runs this circuit `2^(n-1)` times, in a binary tree structure. Next, one measures all qubits but the first one, and denotes the measurement outcome by `ps`. Similarly, one measures the first qubit in the computational basis and denotes the measurement outcome by `success`. One post-selects experimental runs based on `ps` being the all zeros string, and the resulting color of the pixel at `z` is the estimate on the probability of `success` being one based on the measurement outcomes.

## Experiment resources

The following resources are required to perform the experiment (assuming all measurements are performed after all gates have been applied):

  * `q = 2^n`: the number of qubits.
  * `s = p^2*N*2^n`: the number of arbitrary single qubit state preperations required.
  * `g = 4*N*2^(n-1)`: the number of gates that are to be applied in total.
  * `m = p*N*2^n`: the number of single qubit measurements that are to be performed.

## Experiment outcomes



## File structure

There are three files in this folder:

  * `probabilities.py` generates two plots:

    - The left plot indicates the post-selection probabilities.
    - The right plot indicates the success probability of the experiment, given that the post selection succeeded.

  * `simulation.py` does the same thing, but it adds the fact that the measurement outcomes are random.
