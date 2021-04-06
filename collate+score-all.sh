#!/usr/bin/env bash

for subdir in ./runs_old_2/*$1*/; do ./runner.py refresh --run-folder=runs_old_2 "${subdir:13:-1}"; ./runner.py score "${subdir:7:-1}"; done;
