#!/bin/bash

FOLDER=$1
COMMAND=$2

echo "running ./runner.py $COMMAND in folder $FOLDER"

eval "$(conda shell.bash hook)"
for condaenv in qiskit qiskit-17 qiskit-old; do
    conda activate $condaenv
    echo "using environment $condaenv with `pip freeze | grep qiskit==`"
    conda deactivate
done
echo ""

find $FOLDER -type d -name 'IBM*Platonic*' ! -path '*obsolete*' -print0 | 
    while IFS= read -r -d '' folder; do 
        run_folder=`echo $folder | rev | cut -d/ -f2- | rev`
        run=`echo $folder | rev | cut -d/ -f1 | rev`
        echo "trying to run $run in $run_folder"
        
        SUCC="false"
        for condaenv in qiskit qiskit-17 qiskit-old; do
            conda activate $condaenv
            ./runner.py $COMMAND --run_folder=$run_folder $run
            succ=$?
            conda deactivate

            if [ "$succ" = 0 ]; then
                echo "$result"
                SUCC="true"
                break
            fi
        done
        if [ "$SUCC" = "false" ]; then
            echo  -e "\033[31;5mNO ENVIRONMENT WORKED\033[0m"
        else
            echo  -e "\033[32;5m$condaenv ENVIRONMENT WORKED\033[0m"
        fi

        echo ""
    done
