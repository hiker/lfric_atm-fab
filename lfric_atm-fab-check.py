import sys
import os

fp = open('PET0.lfric_atm.Log')
for line in fp:
    line = line.split()
fp.close()

#def add_task(task, tasks):
#    add = True
#    for tt in tasks:
#        if tt == task:
#            add = False
#    if add:
#        tasks.append(task)

# remove the module, object and temporary files created by the builds in order
# to cut down on inode and storage usage
#os.system('cd /scratch/hc46/hc46_gitlab/cylc-run/lfric_atm_nightly/work/1/')
#os.system('find . -type f -name "*.mod" -delete')
#os.system('find . -type f -name "*.o" -delete')
#os.system('find . -type f -name "*.t" -delete')
#os.system('cd /scratch/hc46/hc46_gitlab/cylc-run/lfric_atm_nightly')

# get the svn revision number - dumped into the ~/cylc-run directory during the run stage
#fp = open('/scratch/hc46/hc46_gitlab/cylc-run/lfric_atm_nightly/revision')
#revision = fp.readline().rstrip('\n')
#fp.close()

#path = "/scratch/hc46/hc46_gitlab/cylc-run/lfric_atm_nightly/log/suite/"

#failed_tasks = []
#passed_tasks = []

#fp = open(path + "log", "r")
#for line in fp:
#    line = line.split()
#    nl = len(line)
#    if nl > 3:
#        if len(line[3]) > 15:
#            if line[3][:15] == "[run_lfric_atm_":
#                if line[5] == "failed":
#                    failed_tasks.append(line[3])
#                else:
#                    add_task(line[3], passed_tasks)

#fp.close()

#print("*** Checking lfric_atm nightly rose stem run tasks for failures at revision " + revision + " ***")
#print("*** failed tasks: ")
#for task in failed_tasks:
#    print(task[1:-1])

#fp = open('/scratch/hc46/hc46_gitlab/cylc-run/lfric_atm_nightly/task_failures.txt', "w")
#for task in failed_tasks:
#    fp.write(task[1:-1] + "\n")
#fp.close()

#nf = len(failed_tasks)
#if nf > 0:
#    sys.stderr.write("ERROR: number of failed run tasks: " + str(nf) + "\n")

#print("*** passed tasks: ")
#for task in passed_tasks:
#    print(task[1:-1])

#fp = open('/scratch/hc46/hc46_gitlab/cylc-run/lfric_atm_nightly/task_successes.txt', "w")
#for task in passed_tasks:
#    fp.write(task[1:-1] + "\n")
#fp.close()

#np = len(passed_tasks)
#if np == 0:
#    sys.stderr.write("ERROR: no passing tasks, chech compilation tasks for errors.\n")
#    nf = 999

#sys.exit(nf)
