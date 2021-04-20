# Quantum Benchmarks


## Dependencies

We recommend setting up a separate conda environment per vendor.
Each requires the following dependencies.

    pip install termcolor matplotlib seaborn networkx
    conda install pycairo


## Usage

The benchmarking program is called `runner.py`; available commands can be seen with

    ./runner.py --help

The default output directory is under `./runs`, but can be modified. `./refresh.sh` periodically tries to update the benchmarks (e.g. for IBM); it takes as optional parameter a conda environment to launch first.
The default runs can e.g. be invoked via

    ./run-all-benchmarks.sh ibm cloud ibmq_lima

## License

(c) 2021, Johannes Bausch, Arjan Cornelissen, András Gilyén
