# Quantum Benchmarks


## Dependencies

We strongly recommend having a separate conda environment per vendor.
Each requires the following dependencies.

    pip install termcolor
    conda install pycairo


## Development Instructions

Since python has no strong typing, I recommend you use `pylint` to detect bugs.
Also, use `black` to indent code uniformly before committing.


## Vendor-Specific Notes

### Rigetti

To run the rigetti tests on a local QVM, first launch

    # shell 1
    qvm -S
    # shell 2
    quilc -S

