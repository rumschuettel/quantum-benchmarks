while true
do
  python3 run.py update "$@"
  if [ $? -eq 0 ]
  then
    break
  fi
  sleep 1m
done
echo "Experiment done."
