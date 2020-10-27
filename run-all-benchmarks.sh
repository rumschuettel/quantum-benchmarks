#!/usr/bin/env bash

VENDOR="$1"
MODE="$2"
DEVICE="$3"

echo "$VENDOR, $MODE, $DEVICE"

# run
./runner.py benchmark "$VENDOR" "$MODE" "$DEVICE" Bell-Test -s 8192

./runner.py benchmark "$VENDOR" "$MODE" "$DEVICE" Schroedinger-Microscope -ps 1 -p 32 -s 4096
./runner.py benchmark "$VENDOR" "$MODE" "$DEVICE" Schroedinger-Microscope -ps 2 -p 32 -s 4096

./runner.py benchmark "$VENDOR" "$MODE" "$DEVICE" Mandelbrot -ps 1 -p 32 -s 4096
./runner.py benchmark "$VENDOR" "$MODE" "$DEVICE" Mandelbrot -ps 2 -p 32 -s 4096

./runner.py benchmark "$VENDOR" "$MODE" "$DEVICE" Platonic-Fractals -t 1 -m 32 -s 8192
./runner.py benchmark "$VENDOR" "$MODE" "$DEVICE" Platonic-Fractals -t 2 -m 32 -s 8192

./runner.py benchmark "$VENDOR" "$MODE" "$DEVICE" Line-Drawing -n 2 -r 25 -s 8192
./runner.py benchmark "$VENDOR" "$MODE" "$DEVICE" Line-Drawing -n 4 -r 25 -s 8192
./runner.py benchmark "$VENDOR" "$MODE" "$DEVICE" Line-Drawing -n 8 -r 25 -s 8192
./runner.py benchmark "$VENDOR" "$MODE" "$DEVICE" Line-Drawing -n 16 -r 25 -s 8192

