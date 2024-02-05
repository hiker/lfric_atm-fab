#!/bin/bash

qsub lfric_atm-fab-run.pbs
found=0
while [ $found == 0 ]
do
  test -f timer.txt && found=1
done
echo "Run done!"
