#!/usr/bin/env bash

DEVICE="$1"

echo $DEVICE

# run
./runner.py benchmark ibm cloud "$DEVICE" Schroedinger-Microscope -ps 2 -p 32 -s 4096
./runner.py benchmark ibm cloud "$DEVICE" Mandelbrot -ps 2 -p 32 -s 4096
