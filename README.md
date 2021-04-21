# Quantum Benchmark Suite


## Dependencies

We recommend setting up a separate conda environment per vendor; supported are IBM (qiskit), Google (cirq), Rigetti (forest) and Amazon (braket). Each requires the following dependencies.

    pip install termcolor matplotlib seaborn networkx
    conda install pycairo


## Usage

The benchmarking program is called `runner.py`; available commands can be seen with

    ./runner.py --help

The default output directory is under `./runs`, but can be modified. 

There are also some bash scripts included that can be used on linux systems to automate some task. The script `./refresh.sh` periodically tries to update the benchmarks (e.g. for IBM); it takes as optional parameter a conda environment to launch first.
The default runs can also be invoked via the script

    ./run-all-benchmarks.sh ibm cloud ibmq_lima

## License

(c) 2021, Johannes Bausch, Arjan Cornelissen, András Gilyén
