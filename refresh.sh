#!/usr/bin/env bash

if [ ! -z "$1" ]; then
    CONDA_BASE=$(conda info --base)
    source "$CONDA_BASE/etc/profile.d/conda.sh"
    conda activate $1
fi

function check() {
    while read -r line
    do
        # clean color codes
        line=$(echo "$line" | sed -r "s/\x1B\[([0-9]{1,2}(;[0-9]{1,2})?)?[mGK]//g")

        if [[ $line =~ ^IBM- ]]; then
            lastline="IBM"

            path=$(echo "$line" | cut -f1 -d ":")
            todo=$(echo "$line" | cut -f2 -d " ")
            scheduled=$(echo "$line" | cut -f3 -d " ")

            continue
        fi

        if [[ $lastline == "IBM" ]]; then
            lastline="info"

            # read in info json
            mode=$(echo "$line" | sed "s/'/\"/g" | jq -r ".mode")
            device=$(echo "$line" | sed "s/'/\"/g" | jq -r ".device")

            if (( $todo > 0 || $scheduled > 0 )); then
                if [[ "$mode" == "Cloud" ]]; then
                    echo "resuming $path on $device"
                    cmd="timeout 2m ./runner.py resume \"$path\""
                    echo "$cmd"
                    eval $cmd
                    return
                fi
            fi
        fi
    done < <(./runner.py status)
}

function on_ctrl_c() {
    echo "TERMINATING"
    exit 0
}

trap 'on_ctrl_c' SIGINT

# check forever
while :; do
    check
    sleep 30
done
