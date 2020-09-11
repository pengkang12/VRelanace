from skopt import gp_minimize
from skopt import Optimizer
import skopt.utils as skopt_utils
import numpy as np
import os
import sys
import json
import warnings
if not sys.warnoptions:
    warnings.simplefilter("ignore")

cpu_limit_filename="/tmp/bo_cpulimit.txt"
input_app_name = "/tmp/skopt_app_name.txt"
model_filename = "/tmp/skopt.model"
threshold = [50, 200]

def change_cpu(kubename="test", quota=40000, hostname="kube-slave1"):
    os.system("ssh -t {0} 'echo syscloud | sudo -S bash cpu.sh {1} {2}' 2>&1".format(hostname, kubename, quota))

def get_cpu_info(kubename="test", quota=40000, hostname="kube-slave1"):
    os.system("ssh -t {0} 'echo syscloud | sudo -S bash cpu_info.sh {1} {2}'".format(hostname, kubename, quota))

def check_cpu(arr):
    for a in arr:
        if  a< 100 or a > 4000:
            return False
    return True

def normalized(a):
    ret = []

    total = sum(a)
    if total > 4000:
        a = [int((4000/total)*val) for val in a]
        print(sum(a)) 
    for v in a:
        t = int(v/50 + 2)*5000
        if t >= 395000:
            t = 395000
        if t <= 10000:
            t = 10000

        ret.append(t)
    return ret

def bo_function(app_info):
    t = [] # measured tail latency 
    throughput = []
    motivation = [] # we need to allocate more cpu or less cpu for different application.
    #use x to update the container, and read new tail latency. 
    for key, value in app_info.items():
        t += value["latency"],
        throughput += value['throughput'],
        motivation += 0,
    ret = 0       

    stop_update = False
    for i in range(len(app_name)):
        ret += (t[i]-threshold[i])*(t[i]-threshold[i])/(threshold[i]**2)
        #ret += (throughput[i]/10000)**2
        if abs(t[i]-threshold[i]) > 50:
           #if t[i] - threshold[i] < 0:
           #    ret += 10*(t[i]-threshold[i]/threshold[i])
           stop_update = True
        if t[i] - threshold[i] > 0:
            motivation[i] = 1
        else:
            motivation[i] = -1
    print("latency is {}".format(t))
    if stop_update == False:
        return motivation, ret, True
    return motivation, ret, False

def ask_BO(measured, keys, motivation, last_cpu_limit):
    suggested = []
    count = 0
    while count < 10:
        suggested = opt.ask()
        print('iteration:', suggested, measured)
        if sum(suggested) > 4000:
             opt.tell(suggested, sum(suggested))
             count += 1
             continue
        if check_cpu(suggested) == True:
            break
        count += 1
    
     
    # use new kube cpu quota to system.    
    print('iteration:', suggested, measured, keys, last_cpu_limit)
    if motivation[0] > 0 and sum(suggested) < sum(last_cpu_limit):
        suggested = [(50+val) for val in last_cpu_limit] 
    if motivation[0] < 0 and sum(suggested) > sum(last_cpu_limit):
        suggested = [(val-50) for val in last_cpu_limit] 
    suggested = normalized(suggested)
    print(suggested)
    for i in range(len(keys)):
        change_cpu(keys[i], suggested[i]) 
    print("update model")
    with open(cpu_limit_filename, "a") as f2:
        f2.write(",".join([ str(int(i/100)) for i in suggested])+"\n") 
 
def read_measured_data(app_info, keys):
    with open(cpu_limit_filename) as f1:
        for line in f1:
            pass
        cpu = line.split(",") 
    last_cpu_limit = [int(i) for i in cpu]
    # peng's method
    measured = [] 
    for key in keys:
        for value in app_info.values():
            if key in value["cpu_usage"]:
                #measured.append(value['cpu_usage'][key]+50*value['capacity'][key])
                measured.append(int((value['cpu_usage'][key])/50+1)*50)
 
    print("last cpu limit {}, measured cpu {}".format(last_cpu_limit, measured))
    return last_cpu_limit, measured

def read_container_info():
    app_info = {}
    for name in app_name:
        input_filename = "/tmp/skopt_input_{}.txt".format(name)
        with open(input_filename) as f:
            for line in f:
                pass
            app_info[name] = json.loads(line) 
    print(app_info) 
    
    # we use lexical sort for container. 
    keys = []
    for key, value in app_info.items():
        for key1, val1 in value["cpu_usage"].items():
            keys.append(key1)
    keys.sort()
    return app_info, keys


#0. read application's name
app_name = []
with open(input_app_name) as f:
    for line in f:
        app_name.append(line.rstrip())
        pass
 
#1. first load existed optimization model or build a new model
# when we first time use model
opt = None
if os.path.exists(model_filename):
    opt = skopt_utils.load(model_filename)
    print("read model")
else:
    # default setting: there are three workers for each application, cpu range is from 200m to 500m.
    restriction=[]
    for i in range(len(app_name)):
        for j in range(3):
            restriction += [(100, 3950)]
    opt = Optimizer(restriction, n_initial_points=2, acq_func="gp_hedge", base_estimator="GP")
    app_info, keys = read_container_info()    
    ask_BO([], keys, [0], []) 
    skopt_utils.dump(opt, model_filename)
    sys.exit()

#3. read input data from file'
app_info, keys = read_container_info()
cpu = []
measured = []

last_cpu_limit, measured = read_measured_data(app_info, keys)

motivation, y, stop = bo_function(app_info)
opt.tell(measured, y)
if stop == False:
    print(y, stop)
    ask_BO(measured, keys, motivation, last_cpu_limit)
else:
    print("update model partially")
    for i in range(len(keys)):
        x = abs((last_cpu_limit[i]- measured[i])/measured[i])
        if x >= 0.2:
            last_cpu_limit[i] = int(measured[i]*1.25/50)*50
            change_cpu(keys[i], last_cpu_limit[i]*100) 
            get_cpu_info(keys[i], last_cpu_limit[i]*100)    
    with open(cpu_limit_filename, "a") as f2:
        f2.write(",".join([ str(i) for i in last_cpu_limit])+"\n") 
    print("new cpu limit is ", last_cpu_limit)
    
# save the model
skopt_utils.dump(opt, model_filename)
print("-----------------------------------------------------------------") 
