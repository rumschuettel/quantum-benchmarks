for f in runs/*
do
  echo ${f##*/}
  ./runner.py score ${f##*/}
done
