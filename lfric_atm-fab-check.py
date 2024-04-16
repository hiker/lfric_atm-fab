import sys
import os

# print out current directory
print(f"current dir: {os.getcwd()}")

# check gungho_model and lfric_atm runs 
fp = open('job.log','r')

failed = 1
gungho_failed = 1
lfric_atm_failed = 1
for line in fp:
    line = line.split()
    if len(line) < 3:
        continue
    if line[-2] == 'gungho_model' and line[-1] == 'completed.':
        print('gungho_model run succeeded')
        gungho_failed = 0    
    if line[-2] == 'lfric_atm' and line[-1] == 'completed.':
        print('lfric_atm run succeeded')
        lfric_atm_failed = 0
if gungho_failed == 0 and lfric_atm_failed == 0:
    failed == 0 
fp.close()

if failed:
    if gungho_failed:
        print('gungho_model run failed')
    if lfric_atm_failed:
        print('lfric_atm run failed')

sys.exit(failed)
