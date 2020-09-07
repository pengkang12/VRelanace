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
threshold = [100, 200]

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
    for v in a:
        t = int(v/50 + 1)*5000
        if t >= 395000:
            t = 395000
        if t <= 10000:
            t = 10000

        ret.append(t)
    return ret

def bo_function(app_info):
    t = [] 
    #use x to update the container, and read new tail latency. 
    for key, value in app_info.items():
        t.append(value["latency"]) 
    ret = 0

    stop_update = False
    for i in range(len(app_name)):
        ret += (t[i]-threshold[i])*(t[i]-threshold[i])/(threshold[i]**2)
        if abs(t[i]-threshold[i]) > 50:
           stop_update = True
    print("latency is {}".format(t))
    if stop_update == False:
        return ret, True
    return ret, False

def ask_BO(measured, keys):
    suggested = []
    count = 0
    while count < 10:
        suggested = opt.ask()
        print('iteration:', suggested, measured)
        if check_cpu(suggested) == True:
            break
        count += 1
    else:
        sys.exit()

    suggested = normalized(suggested)
    # use new kube cpu quota to system.    
    print('iteration:', suggested, measured, keys)

    for i in range(len(keys)):
        change_cpu(keys[i], suggested[i]) 
    print("update model")
    with open(cpu_limit_filename, "a") as f2:
        f2.write(",".join([ str(int(i/100)) for i in suggested])+"\n") 
 
def read_measured_data():
    with open(cpu_limit_filename) as f1:
        for line in f1:
            pass
        cpu = line.split(",") 
    print(cpu) 
    measured = [int(i) for i in cpu]
    print(measured) 
    """
    for key in keys:
        for value in app_info.values():
            if key in value["cpu_usage"]:
                measured.append(value['cpu_usage'][key]*value['capacity'][key])
    """
    return measured

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
    opt = Optimizer(restriction, n_initial_points=5, acq_func="gp_hedge", base_estimator="GP")
    app_info, keys = read_container_info()    
    ask_BO([], keys) 
    skopt_utils.dump(opt, model_filename)
    sys.exit()

#3. read input data from file'
app_info, keys = read_container_info()
cpu = []
measured = []

measured = read_measured_data()

y, stop = bo_function(app_info)
if stop == False:
    opt.tell(measured, y)
    print(y, stop)
    print("-----")
    ask_BO(measured, keys)
else:
    print("Don't need to update model")
    os.system("tail -n 1 {0} >> {0}".format(cpu_limit_filename))
    for i in range(len(keys)):
        get_cpu_info(keys[i])
    
# save the model
skopt_utils.dump(opt, model_filename)
 
