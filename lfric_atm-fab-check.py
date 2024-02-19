import sys
import os

fp = open('job.log','r')

failed = 1
for line in fp:
    line = line.split()
    if len(line) < 3:
        continue
    if line[-2] == 'lfric_atm' and line[-1] == 'completed.':
        print('lfric_atm run succeeded')
        failed = 0
fp.close()

if failed:
    print('lfric_atm run failed')

sys.exit(failed)
