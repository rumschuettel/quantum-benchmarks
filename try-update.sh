#!/usr/bin/env bash

cd "$(dirname "$0")";
for f in ./runs/*
do
  id=$(basename $f)
  printf "Checking folder $id..."
  if [ -f "./runs/$id/visualize.pdf" ]
  then
    printf " done.\n"
  else
    printf " invoking update\n"
    ./runner.py resume $id
  fi
done
