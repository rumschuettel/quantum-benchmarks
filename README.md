# Quantum Benchmarks


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

