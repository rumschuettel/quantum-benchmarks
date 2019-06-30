# Schrödinger Microscope

The Schrödinger microscope is an experiment that generates a fractal.

## File structure

There are three files in this folder:

  * `probabilities.py` generates two plots:

    - The left plot indicates the post-selection probabilities for various
    choices of `z`.
    - The right plot indicates the success probability of the experiment, given
    that the post selection succeeded.

  * `ideal.py` runs the experiment a number of times, and gives an idea of
    the type of pictures one can expect to get, using an ideal quantum computer.
  * `ideal_optimized.py` does the same as `with_noise.py`, but the program
    cheats a bit to avoid some unnecessary overhead within `cirq`.
