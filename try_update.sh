cd "$(dirname "$0")";
for f in ./runs/*
do
  id=$(basename $f)
  printf "Checking folder $id..."
  if [ -f "./runs/$id/collated.pickle" ]
  then
    printf " done.\n"
  else
    printf " invoking update\n"
    python3 runner.py resume $id
  fi
done
