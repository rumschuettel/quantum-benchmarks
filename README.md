# Quantum Benchmarks


## Dependencies

We strongly recommend having a separate conda environment per vendor.
Each requires the following dependencies.

    pip install termcolor matplotlib seaborn networkx
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

QPU access is only possible in a QMI (quantum machine image), to which you have
access to via the web interface.

http://docs.rigetti.com/en/stable/advanced_usage.html#advanced-usage

To set up the QMI, use the following steps:

https://www.rigetti.com/qcs/docs/getting-started-with-your-qmi#qmi

Inside the QMI, run

    conda create -n "bench" python=3.7
    pip install pyquil

as well as the requirements listed at the start.
