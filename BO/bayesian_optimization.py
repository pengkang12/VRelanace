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

import helper

model_filename = "/tmp/skopt_model_"
QUOTA = 4000
window = 15

def bo_function(app_info, app_name, cpu_limit, measured_cpu):
    t = [] # measured tail latency 
    throughput = []
    motivation = [] # we need to allocate more cpu or less cpu for different application.
    #use x to update the container, and read new tail latency. 
    ret_y = app_info[app_name]["latency"] - helper.threshold[app_name]
    
    is_violate_target = False
    location = app_info[app_name]["container_loc"]
    app_measured_cpu = [measured_cpu[loc] for loc in location]
    app_cpu_limit = [cpu_limit[loc] for loc in location]
    
    is_violate_target = True
    
    if ret_y > 0 or sum(app_measured_cpu)/ sum(app_cpu_limit) < 0.8:
        is_violate_target = True
        pass
    #return ret_y, is_violate_target
    if ret_y > 0:
        ret_val = max(0, ret_y)+ sum(cpu_limit)/QUOTA 
    else:
        ret_val = -1 * ret_y * sum(cpu_limit)/QUOTA 
    return ret_val, is_violate_target
 

def ask_model(opt, capacity, history_cpu, history_latency, location):
    suggested = []
    count = 0
    while count < 5:
        suggested = opt.ask(strategy='cl_min')
        
        #use history data to update model and ask again
        min_one = min(suggested)
        for i in range(len(suggested)):
            if suggested[i] == min_one:
                break 

        print("ask model ", min_one, count, suggested)
        need_ask = False
        # check bottleneck, if minimum cpu limit from suggestion is less than history cpu limit which violate SLO. We need to 
        # ask again
        for index in range(len(history_latency)):
            if index < len(history_cpu) and history_cpu[index][location[i]] > min_one and history_latency[index] > 100:
                opt.tell(suggested, history_latency[index]-100+min_one)
                need_ask = True 
                count += 1
                print("suggest less than history ", suggested, history_cpu[index])
                if count == 4:
                    suggested = [ history_cpu[index][loc] for loc in location]
                break
        # check overprovision. if minimum cpu limit from suggestion is great than maximum cpu limit from history and this historical cpu limit is satisfied SLO, we need to ask again. 
        for index in range(len(history_latency)):
            if index < len(history_cpu) and history_latency[index] < 100 and max(history_cpu[index]) < min_one :
                opt.tell(suggested, (100-history_latency[index])*sum(suggested))
                need_ask = True 
                count += 1
                if count == 4:
                    suggested = [ history_cpu[index][loc] for loc in location]
                print("suggest greater history ", suggested, history_cpu[index])
                break
        
        if max(suggested)/ min(suggested) > 5:
            count += 1
            continue
        if need_ask == False:
            break

        print('iteration:', suggested)
        """
        if sum(suggested) > QUOTA:
             opt.tell(suggested, sum(suggested))
             count += 1
             continue
        count += 1
        """
    print(capacity, suggested)
    if sum(suggested) > QUOTA:
        min_cpu = min(suggested)
        suggested = [min_cpu*capacity[key] for key in sorted(capacity.keys())]   
    return suggested 

def check_history_cpu_limit(history_cpu, suggest, history_latency, location, app_name):
    ret_cpu = suggest  
    total_cpu = sum(suggest)
    if len(history_cpu) > 20:
        cpu = history_cpu[-20:]
        latency = history_latency[-20:]
    for i in range(len(history_cpu)):
        tmp_cpu = [history_cpu[i][j] for j in location]
        tmp_sum_cpu = sum(tmp_cpu)
        if history_latency[i] < helper.threshold[app_name] and tmp_sum_cpu <= total_cpu:
            total_cpu = tmp_sum_cpu
            ret_cpu = tmp_cpu
    return ret_cpu 
                 
def bo_model(app_name, app_info, cpu_limit, measured_cpu, container_name_list, latency, history_cpu): 
    #1. first load existed optimization model or build a new model
    # when we first time use model
    opt = None
    model_file = model_filename+app_name
    if os.path.exists(model_file) == False:
        restriction=[]
        for j in range(3):
            restriction += [(100, QUOTA)]
        #opt = Optimizer(restriction, n_initial_points=2, acq_func="gp_hedge", base_estimator="GP")
        opt = Optimizer(restriction, n_initial_points=0, acq_func="EI", base_estimator="GP")
 
        print("initialize model {}".format(app_name))
    else:
        opt = skopt_utils.load(model_file)
        print("read model for {}".format(app_name))
        
    y, is_violate_target= bo_function(app_info, app_name, cpu_limit, measured_cpu)
    location = app_info[app_name]["container_loc"]
    app_measured_cpu = [measured_cpu[loc] for loc in location]
    app_cpu_limit = [cpu_limit[loc] for loc in location]
 
    #opt.tell(app_measured_cpu, y)
    opt.tell(app_cpu_limit, y)
   
    if is_violate_target == True:
       # save the model
        suggest = ask_model(opt, app_info[app_name]['capacity'], history_cpu, latency, location)

        suggest = helper.normalized(suggest)
        print("normalized ", suggest)      
        #suggest = check_history_cpu_limit(history_cpu, suggest, latency, location, app_name)
        print("check hisotry ", suggest, location, cpu_limit)		
        i = 0
        for loc in location:
            if int(suggest[i]) != cpu_limit[loc]:
                cpu_limit[loc] = int(suggest[i])
            i += 1
    skopt_utils.dump(opt, model_file)
    print("-----------------------------------------------------------------") 
    return cpu_limit

def find_min_index(arr1, location, latency ):
    bad_arr1 = []
    for i in range(len(arr1)):
        if latency[i] > 100:
            bad_arr1 += arr1[i],
    min_i = -1
    min_sum = helper.QUOTA
    for i in range(window):
        tmp_sum = sum([arr1[i][loc] for loc in location])
        if tmp_sum < min_sum and latency[i] < 100 and arr1[i] not in bad_arr1:
            print(tmp_sum, i, arr1[i])
            min_i = i
            min_sum = tmp_sum
    
    print(arr1[min_i], bad_arr1)  
    return min_i 

def system_control():
    # read container information    
    app_info, container_name_list, latency = helper.read_container_info()
  
    history_cpu, measured_cpu = helper.read_measured_data(app_info, container_name_list)
    
    cpu_limit = history_cpu[-1].copy()    
    print('iteration: measured is {}, last cpu limit is {}'.format(measured_cpu, cpu_limit))

    # consistly violate SLO
    need_recalculate = False
    for key in sorted(app_info.keys()):
        if len(latency) > 2 and latency[key][-2] > 100 and latency[key][-1] > 100:
            need_recalculate = True

    if len(history_cpu) < window or need_recalculate:
        for key in sorted(app_info.keys()):
            value = app_info[key]
            cpu_limit = bo_model(key, app_info, cpu_limit, measured_cpu, container_name_list, latency[key], history_cpu) 
        # normalize again for cpu limit
        if sum(cpu_limit) > helper.QUOTA:
            cpu_limit = helper.normalized(cpu_limit)      
            pass

        print('iteration: update cpu limit is {}'.format(cpu_limit))
        for i in range(len(cpu_limit)):
            if (history_cpu[-1][i]) != cpu_limit[i]:
                helper.change_cpu(container_name_list[i], cpu_limit[i]*100)
    else:
        history_cpu = history_cpu[-window:]
        cpu_limit = []
        for key in sorted(app_info.keys()):
            latency1 = latency[key][-window:]
            value = app_info[key]
            location = value["container_loc"]
            index = find_min_index(history_cpu, location, latency1)
            cpu_limit += [history_cpu[index][loc] for loc in location]
        print("this is find optimal value", cpu_limit, history_cpu[-1])
        for i in range(len(cpu_limit)):
            if history_cpu[-1][i] != cpu_limit[i]:
                helper.change_cpu(container_name_list[i], cpu_limit[i]*100)
 
    helper.write_cpu_limit_file(cpu_limit)
    print("end this iteration\n\n")

import timeit

start = timeit.default_timer()

system_control()

stop = timeit.default_timer()

print('Time: ', stop - start)  
