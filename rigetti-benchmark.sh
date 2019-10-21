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
./runner.py benchmark rigetti cloud "$ENGAGED_QPU" Schroedinger-Microscope -ps 1 -p 32 -s 1024
./runner.py benchmark rigetti cloud "$ENGAGED_QPU" Platonic-Fractals -ps 1 -p 32 -s 1024
