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
threshold = [100, 100]
threshold_range = 25
QUOTA = 4000

def change_cpu(kubename="test", quota=40000, hostname="kube-slave1"):
    os.system("ssh -t -t {0} 'echo syscloud | sudo -S bash cpu.sh {1} {2}' 2>&1".format(hostname, kubename, quota))

def get_cpu_info(kubename="test", quota=40000, hostname="kube-slave1"):
    os.system("ssh -t -t {0} 'echo syscloud | sudo -S bash cpu_info.sh {1} {2}'".format(hostname, kubename, quota))
    pass
def check_cpu(arr):
    for a in arr:
        if  a< 100 or a > QUOTA:
            return False
    return True


def normalized(a):
    ret = []

    total = sum(a)
    if total > QUOTA:
        a = [int((QUOTA/total)*val) for val in a]
        print(sum(a)) 
    for v in a:
        t = int(v/50 + 1)*5000
        if t >= QUOTA*100:
            t = QUOTA*100 
        if t <= 10000:
            t = 10000

        ret.append(t)
    return ret

def bo_function(app_info, cpu_limit, measured_cpu):
    t = [] # measured tail latency 
    throughput = []
    motivation = [] # we need to allocate more cpu or less cpu for different application.
    #use x to update the container, and read new tail latency. 
    for key, value in app_info.items():
        t += value["latency"],
        throughput += value['throughput'],
        motivation += 0,
    ret_y = 0
    
    is_violate_target = False
    for i in range(len(app_name)):
        tmp = 1*(t[i]-threshold[i])
	#*(t[i]-threshold[i])/(threshold[i]**2)
        #tmp += (throughput[i]/10000)
        if tmp > 0:
            ret_y += tmp
        if t[i]-threshold[i] > 0:
           is_violate_target = True
        if t[i] - threshold[i] > 0:
            motivation[i] = 1*tmp
        else:
            motivation[i] = -1 * tmp
    print("latency is {}".format(t))
    if sum(measured_cpu)/ sum(cpu_limit) < 0.8:
        is_violate_target = True
    return motivation, max(0, ret_y)+ sum(cpu_limit)/QUOTA, is_violate_target

    """ 
    this method is too sensitive to model and the results look very dynamic. 
    total_cpu = 0
    for key, value in app_info.items():
        location = value["container_loc"]
        if sum([measured_cpu[i] for i in location])/ sum([cpu_limit[i] for i in location]) < 0.8:
            is_violate_target = True
            total_cpu += sum(cpu_limit)
        print("app {} : measured {}, cpu_limit {}".format(key, sum([measured_cpu[i] for i in location]), sum([cpu_limit[i] for i in location])))

    if total_cpu == 0:
        total_cpu = QUOTA
    return motivation, max(0, ret_y)+ QUOTA/total_cpu, is_violate_target
    """

"""
max(0, W1*(latency1-threshold1)/threshold1, W2*(latency1-threshold2)/threshold2)) + sum(cpu_limit)/QUATA. 

latency1 = 10
latency2 = 1000
app1: worker1, worker2, worker3.
app2: worker4, worker5, worker6.
total cpu limit = 4000

do first optimization app1 is static workload. worker1 700, worker2 800, worker3 1000.

do second optimization(app1, app2):  app1(700, 1000), app2(100, 4000-2500). 

frequence: slow 


"""

def ask_model():
    suggested = []
    count = 0
    while count <= 10:
        suggested = opt.ask(strategy='cl_min')
        print('iteration:', suggested)
        if sum(suggested) > QUOTA:
             opt.tell(suggested, sum(suggested))
             count += 1
             continue
        if check_cpu(suggested) == True:
            break
        count += 1
    return suggested 

def update_system(measured, keys, motivation, last_cpu_limit, is_violated):
    suggested = ask_model()
    if is_violated == True: 
        # use new kube cpu quota to system.    
        print('iteration: suggeseted is {}, measured is {}, last cpu limit is {}'.format(suggested, measured, last_cpu_limit))
        count = 0 
        """
        """
        suggested = normalized(suggested)
        print("suggested cpu limit is ",suggested)
        for i in range(len(keys)):
            change_cpu(keys[i], suggested[i]) 
        print("update model for Bayesian optimization")
        with open(cpu_limit_filename, "a") as f2:
            f2.write(",".join([ str(int(i/100)) for i in suggested])+"\n") 
    else:    
        print("dont update model")
       
        with open(cpu_limit_filename, "a") as f2:
            f2.write(",".join([ str(i) for i in last_cpu_limit])+"\n") 
        print("new cpu limit is ", suggested)
 
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
                measured.append(value['cpu_usage'][key])
 
    print("last cpu limit {}, measured cpu {}, ratio is {}".format(last_cpu_limit, measured, sum(measured)/sum(last_cpu_limit)))
    return last_cpu_limit, measured

def read_container_info():
    app_info = {}
    for name in app_name:
        input_filename = "/tmp/skopt_input_{}.txt".format(name)
        with open(input_filename) as f:
            for line in f:
                pass
            app_info[name] = json.loads(line) 
    
    # we use lexical sort for container. 
    keys = []
    for key, value in app_info.items():
        for key1, val1 in value["cpu_usage"].items():
            keys.append(key1)
    keys.sort()
    for key, value in app_info.items():
        location = []
        for key1 in value["cpu_usage"].keys():
            loc = 0
            for key2 in keys:
                if key2 == key1:
                    break
                loc += 1
            location.append(loc)
        app_info[key]["container_loc"] = location
    print(app_info) 
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
    # default setting: there are three workers for each application, cpu range is from 100m to maximum.
    restriction=[]
    for i in range(len(app_name)):
        for j in range(3):
            restriction += [(100, QUOTA)]
    opt = Optimizer(restriction, n_initial_points=6, acq_func="gp_hedge", base_estimator="GP")
    app_info, keys = read_container_info()    
    update_system([], keys, [0], [], True) 
    skopt_utils.dump(opt, model_filename)
    sys.exit()

#3. read input data from file'
app_info, keys = read_container_info()
cpu = []
measured = []
print(keys)

last_cpu_limit, measured = read_measured_data(app_info, keys)

motivation, y, is_violate_target= bo_function(app_info, last_cpu_limit, measured)

opt.tell(measured, y)
opt.tell(last_cpu_limit, y)
update_system(measured, keys, motivation, last_cpu_limit, is_violate_target)
    
   
# save the model
skopt_utils.dump(opt, model_filename)
print("-----------------------------------------------------------------") 
