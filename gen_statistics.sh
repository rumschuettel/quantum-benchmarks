#!/bin/bash
for i in {1..100}
do
  echo "Progress: $i/100."
  ./runner.py benchmark google measure_local sparse_simulator_measure_local Schroedinger-Microscope -ps 1 -p 32 -s 128 > /dev/null
done
