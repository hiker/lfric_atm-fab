import sys
import os

fp = open('PET0.lfric_atm.Log','r')

failed = 1
for line in fp:
    line = line.split()
    if line[-2] == 'lfric_atm' and line[-1] == 'completed.':
        print('lfric_atm run succeeded')
        failed = 0
fp.close()

sys.exit(failed)
