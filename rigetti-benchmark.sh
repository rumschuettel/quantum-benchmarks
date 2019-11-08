#!/usr/bin/env bash

# get engaged qpu
ENGAGED_QPU=`./rigetti-get-engaged-qpu.sh`
ERR=$?

if [ "$ERR" != "0" ]; then
    echo "no QPU engaged. Error code $ERR"
    exit "$ERR"
fi

echo "QPU engaged: $ENGAGED_QPU"
echo "starting benchmark..."

# run
#time ./runner.py benchmark rigetti cloud "$ENGAGED_QPU" Schroedinger-Microscope -ps 1 -p 32 -s 4096
#time ./runner.py benchmark rigetti cloud "$ENGAGED_QPU" Mandelbrot -ps 1 -p 32 -s 4096
#time ./runner.py benchmark rigetti cloud "$ENGAGED_QPU" Line-Drawing -n 4 -s 4096 -r 128
time ./runner.py benchmark rigetti cloud "$ENGAGED_QPU" Bell-Test --num_shots=8192

#time ./runner.py benchmark rigetti cloud "$ENGAGED_QPU" Schroedinger-Microscope -ps 2 -p 32 -s 4096
#time ./runner.py benchmark rigetti cloud "$ENGAGED_QPU" Mandelbrot -ps 2 -p 32 -s 4096
#time ./runner.py benchmark rigetti cloud "$ENGAGED_QPU" Line-Drawing -n 16 -s 4096 -r 128
