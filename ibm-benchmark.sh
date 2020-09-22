#!/usr/bin/env bash

MODE="$1"
DEVICE="$2"

echo $MODE
echo $DEVICE

# run
./runner.py benchmark ibm "$MODE" "$DEVICE" Schroedinger-Microscope -ps 1 -p 32 -s 4096
./runner.py benchmark ibm "$MODE" "$DEVICE" Schroedinger-Microscope -ps 2 -p 32 -s 4096

./runner.py benchmark ibm "$MODE" "$DEVICE" Mandelbrot -ps 1 -p 32 -s 4096
./runner.py benchmark ibm "$MODE" "$DEVICE" Mandelbrot -ps 2 -p 32 -s 4096

./runner.py benchmark ibm "$MODE" "$DEVICE" Platonic-Fractals -t 1 -m 32 -s 8092
./runner.py benchmark ibm "$MODE" "$DEVICE" Platonic-Fractals -t 2 -m 32 -s 8092

./runner.py benchmark ibm "$MODE" "$DEVICE" Line-Drawing -n 2 -r 25 -s 8092
./runner.py benchmark ibm "$MODE" "$DEVICE" Line-Drawing -n 4 -r 25 -s 8092
./runner.py benchmark ibm "$MODE" "$DEVICE" Line-Drawing -n 8 -r 25 -s 8092
./runner.py benchmark ibm "$MODE" "$DEVICE" Line-Drawing -n 16 -r 25 -s 8092

./runner.py benchmark ibm "$MODE" "$DEVICE" Bell-Test -s 8092
