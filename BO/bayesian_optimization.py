from skopt import gp_minimize
from skopt import Optimizer
from skopt import acquisition
from skopt.learning import GaussianProcessRegressor
from skopt.learning.gaussian_process.kernels import ConstantKernel, Matern
# Gaussian process with Matérn kernel as surrogate model
from sklearn.gaussian_process.kernels import (RBF, Matern, RationalQuadratic,
                                              ExpSineSquared, DotProduct,
                                              ConstantKernel)
import skopt.utils as skopt_utils
import numpy as np
import os
import sys
import json
import warnings
if not sys.warnoptions:
    warnings.simplefilter("ignore")

import helper
import logistic_regression

model_filename = "/tmp/skopt_model_"
RE_QUOTA = 4000/50
noise_level = 0.1
window = 15

def bo_function(app_info, app_name, app_cpu_limit):
    t = [] # measured tail latency 
    throughput = int(int(app_info[app_name]["throughput"])) + 1
    motivation = [] # we need to allocate more cpu or less cpu for different application.
    #use x to update the container, and read new tail latency. 
    ret_y = app_info[app_name]["latency"] - helper.threshold[app_name]
    
    is_violate_target = False
    
    #return ret_y, is_violate_target
    is_violate_target = True
    if ret_y > 0:
        # violate target
        ret_val = max(0, ret_y+100) * sum(app_cpu_limit)/50
    else:
        ret_val = (100-ret_y)*sum(app_cpu_limit)/50
    return int(ret_val), is_violate_target
 

def ask_model(opt, capacity, history_cpu, history_latency):
    suggested = []
    count = 0
    while count < 5:

        count += 1
        suggested = opt.ask(strategy='cl_min')
        #use history data to update model and ask again
        break
        print(suggested)
        suggested = [ 50*int(val) for val in suggested]
        min_one = min(suggested)
        for i in range(len(suggested)):
            if suggested[i] == min_one:
                break 
        print("ask model ", min_one, count, suggested)
        break

        need_ask = False
        # check bottleneck, if minimum cpu limit from suggestion is less than history cpu limit which violate SLO. We need to 
        # ask again
        for index in range(len(history_latency)):
            if index < len(history_cpu) and history_cpu[index][i] > min_one and history_latency[index] > 100:
                opt.tell([int(val/50) for val in suggested], (history_latency[index])*sum(suggested)/50)
                need_ask = True 
                count += 1
                print("suggest less than history ", suggested, history_cpu[index])
                if count == 4:
                    suggested = history_cpu[index]
                break
        # check overprovision. if minimum cpu limit from suggestion is great than maximum cpu limit from history and this historical cpu limit is satisfied SLO, we need to ask again. 
        for index in range(len(history_latency)):
            if index < len(history_cpu) and history_latency[index] < 100 and max(history_cpu[index]) < min_one :
                opt.tell([int(val/50) for val in suggested], (100-history_latency[index])*sum(suggested)/50)
                need_ask = True 
                count += 1
                if count == 4:
                    suggested = history_cpu[index]
                print("suggest greater history ", suggested, history_cpu[index])
                break
        
        if max(suggested)/ min(suggested) > 5:
            continue
        if need_ask == False:
            break

        print('iteration:', suggested)
        
        if sum(suggested) > RE_QUOTA:
             opt.tell([int(val/50) for val in suggested], sum(suggested))
             count += 1
             continue
        count += 1
    if sum(suggested) > RE_QUOTA:
        min_cpu = min(suggested)
        suggested = [min_cpu*capacity[key] for key in sorted(capacity.keys())]   
    suggested = [val*50 for val in suggested]    
    print(capacity, suggested)
 
    return suggested 

def get_bo_model(app_name, throughput):

    category = 3
    if throughput < 35000:
        category = 1
    elif throughput < 70000:
        category = 2 

    model_file = model_filename+app_name + str(category)
 
    if os.path.exists(model_file) == False:
        restriction=[]
        for j in range(3):
            start = 3
            # leave minimum CPU for other app and container
            end = int(RE_QUOTA) - 3*start*len(helper.threshold.keys()) + 2
            restriction += [(start, end)]
      
        # default GP kernel 
        #kernel=1**2 * Matern(length_scale=[1, 1, 1], nu=2.5) + WhiteKernel(noise_level=1),
        #optimizer='fmin_l_bfgs_b',
        #opt = Optimizer(restriction, n_initial_points=2, acq_func="gp_hedge", base_estimator="GP")
        kernels = [1.0 * RBF(length_scale=1.0, length_scale_bounds=(1e-1, 10.0)),
           1.0 * RationalQuadratic(length_scale=1.0, alpha=0.1),
           1.0 * ExpSineSquared(length_scale=1.0, periodicity=3.0,
                                length_scale_bounds=(0.1, 10.0),
                                periodicity_bounds=(1.0, 10.0)),
           ConstantKernel(0.1, (0.01, 10.0)) * (DotProduct(sigma_0=1.0, sigma_0_bounds=(0.1, 10.0)) ** 2),
           1.0 * Matern(length_scale=1.0, length_scale_bounds=(1e-1, 10.0), nu=2.5)]
     
        gpr = GaussianProcessRegressor(kernel=kernels[1], alpha=noise_level ** 2,
                                   normalize_y=True, noise="gaussian",
                                   n_restarts_optimizer=2)
    
        opt = Optimizer(restriction, n_initial_points=1, acq_optimizer="sampling", base_estimator=gpr)
        print("initialize model {}".format(app_name))
    else:
        opt = skopt_utils.load(model_file)
        print("read model for {}".format(app_name))
    return opt             
   
def bo_model(app_name, app_info, app_cpu_limit, measured_cpu, container_name_list, latency, history_cpu): 
    #1. first load existed optimization model or build a new model
    # when we first time use model
    opt = None
    throughput = app_info[app_name]["throughput"]
    opt = get_bo_model(app_name, throughput)    
 
    y, is_violate_target= bo_function(app_info, app_name, app_cpu_limit)
 
    next_x = [ int(val/50)for val in app_cpu_limit]
    res  = opt.tell(next_x, y)
    print("acquisition function ", res.x_iters, res.func_vals)    

    #print("acquisition function ------", res)    
    if len(history_cpu) >= 5 and res and len(res.models) > 1:
        # acquisition 
        gp = res.models[-1]
        curr_x_iters = res.x_iters
        curr_func_vals = res.func_vals
    
        acq = acquisition.gaussian_ei(curr_x_iters, gp, y_opt=np.min(curr_func_vals))
     
        print("acquisition function ", acq, curr_x_iters)    

        next_acq = acquisition.gaussian_ei(res.space.transform([next_x]), gp, y_opt=np.min(curr_func_vals))
        print("next acquistion function ", next_acq)

    if is_violate_target == True:
       # save the model
        suggest = ask_model(opt, app_info[app_name]['capacity'], history_cpu, latency)

        suggest = helper.normalized(suggest)
        print("normalized ", suggest)      
        print("check_hisotry ", suggest, app_cpu_limit)		
        for i in range(len(app_cpu_limit)):
            if int(suggest[i]) != app_cpu_limit[i]:
                app_cpu_limit[i] = int(suggest[i])
    #save model
    category = 3
    if throughput < 35000:
        category = 1
    elif throughput < 70000:
        category = 2 
    skopt_utils.dump(opt, model_filename+app_name+str(category))
    print("-----------------------------------------------------------------") 
    return app_cpu_limit

def find_min_index(arr1, latency, throughput ):
    # we also need to choose maximum throughput
    max_throughput = max(throughput)*0.85
    bad_arr1 = []
    for i in range(len(arr1)):
        if i < len(latency) and latency[i] > 100:
            bad_arr1 += arr1[i],
    min_i = -1
    min_sum = helper.QUOTA
    for i in range(len(arr1)):
        tmp_sum = sum(arr1[i])
        if tmp_sum < min_sum and i < len(latency) and latency[i] < 100 and arr1[i] not in bad_arr1 and throughput[i] >= max_throughput:
            print("choose min index ", tmp_sum, i, arr1[i])
            min_i = i
            min_sum = tmp_sum
    
    print(arr1[min_i], bad_arr1, max_throughput)  
    return min_i 

def is_workload_changed(throughput):
    # check historical throughput whether workload is changed.
    # we only check last 4 data
    length = len(throughput)
    if length < 2:
        return False
    pivot = throughput[-1]
    for i in range(4):
        if length - i  > 0 and abs((throughput[length-1-i] - pivot)/pivot) > 20:
            return True
    return False

def system_control():
    # read container information    
    app_info, container_name_list, latency, throughput = helper.read_container_info()
  
    measured_cpu = helper.read_measured_data(app_info, container_name_list)
    # save cpu limit
    final_cpu_limit = []
    previous_cpu_limit = []

    for key in sorted(app_info.keys()):
        app_name = key
        value = app_info[key]
        location = value["container_loc"]
        history_cpu = helper.read_history_data(app_name) 
        app_cpu_limit = history_cpu[-1].copy()    
        previous_cpu_limit += app_cpu_limit
 
        opt = get_bo_model(app_name, app_info[app_name]["throughput"])    
 
        y, is_violate_target= bo_function(app_info, app_name, app_cpu_limit)
        print(history_cpu) 
        next_x = [ int(val/50)for val in app_cpu_limit]
        res  = opt.tell(next_x, y)
        print("acquisition function ", res.x_iters, res.func_vals)    

        if len(history_cpu) >= 5 and res and len(res.models) > 1:
            # acquisition 
            gp = res.models[-1]
            curr_x_iters = res.x_iters
            curr_func_vals = res.func_vals
    
            acq = acquisition.gaussian_ei(curr_x_iters, gp, y_opt=np.min(curr_func_vals))
     
            print("acquisition function ", acq, curr_x_iters)    

            next_acq = acquisition.gaussian_ei(res.space.transform([next_x]), gp, y_opt=np.min(curr_func_vals))
            print("next acquistion function ", next_acq)
        min_iters = None
        min_vals = 65536*4000
 
        if len(res.func_vals) < 10 or (is_workload_changed(throughput[app_name])):
            print("start phase or workload changed")
            pass
        else:
            for i in range(len(res.func_vals)):
                if res.func_vals[i] > 100*sum(res.x_iters[i]) and min_vals > res.func_vals[i]:
                    min_vals = res.func_vals[i]
                    min_iters = res.x_iters[i]
         
        print("find best configure ", min_vals, min_iters) 
        # first time to training model
        if min_iters:
            app_cpu_limit = [int(val)*50 for val in min_iters]
            final_cpu_limit += app_cpu_limit
            helper.write_best_configuration(app_name, app_info[app_name]['throughput'], app_cpu_limit)
        else: 
            app_cpu_limit = bo_model(key, app_info, app_cpu_limit, measured_cpu, container_name_list, latency[key], history_cpu) 
            final_cpu_limit += app_cpu_limit
            print('{} iteration: update cpu limit is {}'.format(key, final_cpu_limit))
            # todo, make sure the cpu limit shouldn't less than some value if we have low throughput model. 
            # Ex. since we allocate very small cpu limit, this cause the next throughput very low. Then, we will choose wrong model next time. We need to avoid this situation. 
            """
            if len(history_cpu) < 10:
                app_cpu_limit = bo_model(key, app_info, app_cpu_limit, measured_cpu, container_name_list, latency[key], history_cpu) 
                final_cpu_limit += app_cpu_limit
                print('{} iteration: update cpu limit is {}'.format(key, final_cpu_limit))
            elif len(history_cpu) == 10:
                history_cpu = history_cpu[-window:]
                #for key in sorted(app_info.keys()):
                latency_app = latency[key][-window:]
                throughput_app = throughput[key][-window:]
                index = find_min_index(history_cpu,  latency_app, throughput_app)
                if index >= 0:
                    app_cpu_limit = history_cpu[index]
                    final_cpu_limit += app_cpu_limit
                    print("{} this is find optimal value {}, {}".format(key, final_cpu_limit, history_cpu[-1]))
                else:
                    # ask and training again
                    app_cpu_limit = bo_model(key, app_info, app_cpu_limit, measured_cpu, container_name_list, latency[key], history_cpu) 
                    final_cpu_limit += app_cpu_limit
            else:
                # empty history cpu
                app_cpu_limit = history_cpu[-1]
                final_cpu_limit += app_cpu_limit
                # write result to best_configuration
                helper.write_best_configuration(app_name, app_info[app_name]['throughput'], app_cpu_limit)
            """
    final_cpu_limit = helper.normalized(final_cpu_limit)
    print('final cpu limit is {}'.format(final_cpu_limit))


    for key in sorted(app_info.keys()):
        loc = app_info[key]["container_loc"]
        app_cpu_limit = [final_cpu_limit[l] for l in loc]
        helper.write_history_data(app_cpu_limit, key) 
         
    for i in range(len(previous_cpu_limit)):
        if previous_cpu_limit[i] != final_cpu_limit[i]:
            helper.change_cpu(container_name_list[i], final_cpu_limit[i]*100)
    
    helper.write_cpu_limit_file(final_cpu_limit)
 
    print("end this iteration\n\n")

import timeit

start = timeit.default_timer()

system_control()

stop = timeit.default_timer()

print('Time: ', stop - start)  
