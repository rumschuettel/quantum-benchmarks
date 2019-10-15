#!/usr/bin/env bash

cd "./runs/$1/jobs"
find . -type f -name "*.circuit.pickle" -printf '%P\n' | tar -cf circuits.tar.gz --strip-components=2 -T -
mv circuits.tar.gz "../../../circuits.$1.tar.gz"
cd -
