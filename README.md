# Quantum Benchmarks


## Dependencies

We recommend setting up a separate conda environment per vendor.
Each requires the following dependencies.

    pip install termcolor matplotlib seaborn networkx
    conda install pycairo


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

as well as the requirements listed at the start.


### IBM

To work with run benchmarks from pre 2020 try to look at `iterate-all-ibm.sh`, which attempts to run a command using various conda environments; it appears for our runs three environments with `qiskit==>.20,.17,.14.1` seems to suffice.


## License

(c) 2021, Johannes Bausch, Arjan Cornelissen, András Gilyén
