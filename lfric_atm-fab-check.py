import sys
import os

fp = open('PET0.lfric_atm.Log','r')
for line in fp:
    line = line.split()
fp.close()
print(line)

failed = 1
if line[-2] == 'lfric_atm' and line[-1] == 'completed.':
    failed = 0
    print('lfric_atm run succeeded')
else:
    print('lfric_atm run failed')

sys.exit(failed)
