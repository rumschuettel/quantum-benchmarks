#!/usr/bin/env bash

TMP_DIR=$(mktemp -d -t qbench-XXXXXXXXXX)

echo "RIGETTI TEST"
echo "storing temporary files in $TMP_DIR"

./runner.py --help
./runner.py info vendor rigetti

echo "RIGETTI SCHROEDINGER MICROSCOPE"
./runner.py benchmark --run_folder="$TMP_DIR" rigetti measure_local 8q-qvm Schroedinger-Microscope
./runner.py benchmark --run_folder="$TMP_DIR" rigetti statevector WavefunctionSimulator Schroedinger-Microscope

echo "RIGETTI PLATONIC FRACTALS"
./runner.py benchmark --run_folder="$TMP_DIR" rigetti measure_local 8q-qvm Platonic-Fractals

echo "RIGETTI JOB STATUS"
./runner.py status --run_folder="$TMP_DIR"

echo "RIGETTI TEST COMPLETED."
echo "cleanup..."
rm -r "$TMP_DIR"
echo "done."