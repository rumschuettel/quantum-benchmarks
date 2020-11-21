#!/usr/bin/env bash

for subdir in ./runs/*/; do ./runner.py refresh "${subdir:7:-1}"; ./runner.py score "${subdir:7:-1}"; done;
