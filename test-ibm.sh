#!/usr/bin/env bash

TMP_DIR=$(mktemp -d -t qbench-XXXXXXXXXX)

echo "IBM TEST"
echo "storing temporary files in $TMP_DIR"

./runner.py --help
./runner.py info vendor ibm

echo "IBM SCHROEDINGER MICROSCOPE"
./runner.py benchmark --run_folder="$TMP_DIR" ibm statevector statevector_simulator Schroedinger-Microscope
./runner.py benchmark --run_folder="$TMP_DIR" ibm measure_local qasm_simulator Schroedinger-Microscope

echo "IBM PLATONIC FRACTALS"
./runner.py benchmark --run_folder="$TMP_DIR" ibm measure_local qasm_simulator Platonic-Fractals

echo "IBM VQE"
./runner.py benchmark --run_folder="$TMP_DIR" ibm statevector statevector_simulator VQE-Hamiltonian --qubits=4 --rounds=10
./runner.py benchmark --run_folder="$TMP_DIR" ibm measure_local qasm_simulator VQE-Hamiltonian --qubits=4 --rounds=10

echo "IBM JOB STATUS"
./runner.py status --run_folder="$TMP_DIR"

echo "IBM TEST COMPLETED."
echo "cleanup..."
rm -r "$TMP_DIR"
echo "done."