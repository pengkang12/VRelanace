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
import random
if not sys.warnoptions:
    warnings.simplefilter("ignore")
import timeit
import helper
import logistic_regression

model_filename = "/tmp/skopt_model_"
RE_QUOTA = 4000/50
noise_level = 0.1
window = 15

def bo_function(app_info, app_name, app_cpu_limit):
    t = [] # measured tail latency 
    throughput = int(app_info[app_name]["throughput"]/1000)/100.0
    motivation = [] # we need to allocate more cpu or less cpu for different application.
    #use x to update the container, and read new tail latency. 
    ret_y = app_info[app_name]["latency"] - helper.threshold[app_name]
    
    #return ret_y, is_violate_target
    if app_info[app_name]["latency"] > helper.threshold[app_name]:
        # violate target
        ret_val = app_info[app_name]["latency"] * sum(app_cpu_limit)/50
    else:
        ret_val = (helper.threshold[app_name]- app_info[app_name]["latency"])*sum(app_cpu_limit)/50
    return int(ret_val)
 

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

def choose_category(throughput):
    category = 8
    if throughput < 20000:
        category = 1
    elif throughput < 45000:
        category = 2 
    elif throughput < 55000:
        category = 3 
    elif throughput < 65000:
        category = 4 
    elif throughput < 75000:
        category = 5
    elif throughput < 85000:
        category = 6
    elif throughput < 90000:
        category = 7
    return category


def get_bo_model(app_name, throughput, container_number):

    category = choose_category(throughput)

    model_file = model_filename+app_name + str(category)
 
    if os.path.exists(model_file) == False:
        restriction=[]
        for j in range(container_number):
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
        category = choose_category(throughput)
        skopt_utils.dump(opt, model_filename+app_name+str(category))
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
    opt = get_bo_model(app_name, throughput, len(app_info[app_name]['container_loc']))    
 
    y = bo_function(app_info, app_name, app_cpu_limit)
 
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

    #if app_info[app_name]["latency"] > helper.threshold[app_name]:
    if True:
        # save the model
        suggest = ask_model(opt, app_info[app_name]['capacity'], history_cpu, latency)
        if suggest in res.x_iters:
            suggest = choose_best_from_model(res, app_name, app_info)
        else:
            suggest = helper.normalized(suggest)
        print("normalized ", suggest)      
        # avoid this kind of situation, when we have a very huge throughput, we allocate very small cpu.
        suggest = helper.compare_best_configuration(app_name, throughput, suggest)
        print("check_hisotry ", suggest, app_cpu_limit)		
        for i in range(len(app_cpu_limit)):
            if int(suggest[i]) != app_cpu_limit[i]:
                app_cpu_limit[i] = int(suggest[i])
        

    #save model
    category = choose_category(throughput)
    skopt_utils.dump(opt, model_filename+app_name+str(category))
    print("-----------------------------------------------------------------") 
    return app_cpu_limit

def is_workload_changed(throughput):
    # check historical throughput whether workload is changed.
    # we only check last 4 data
    length = len(throughput)
    print(throughput)
    if length < 3:
        return False
    pivot = throughput[-1]
    for i in range(3):
        if pivot == 0 or (length - i  > 0 and abs((throughput[length-1-i] - pivot)/pivot) > 0.2):
            return True
    return False

def choose_best_from_model(res, app_name, app_info):
    min_iters = None
    min_vals = 65536*400
    ratio = 1
    if int(app_info[app_name]["throughput"]) > 50000:
        ratio = 2
 
    for i in range(len(res.func_vals)):
        if res.func_vals[i] < helper.threshold[app_name]*sum(res.x_iters[i]) and min_vals > sum(res.x_iters[i]):
            min_vals = sum(res.x_iters[i])
            min_iters = res.x_iters[i]
    # choose best from all case that violate SLO.
    if not min_iters:
        for i in range(len(res.func_vals)):
            if res.func_vals[i] < min_vals:
                min_vals = res.func_vals[i]
                min_iters = [x+ratio for x in res.x_iters[i]]
                

    # make sure when throuphput is in the upper bound. Our model training in the lower bound. Optimization this situation.
    throughput_tmp = int(app_info[app_name]["throughput"]/1000)/100.0
    if min_iters is not None and throughput_tmp > (min_vals - int(min_vals)) :
        print("min_iters: {} {}".format(throughput_tmp, min_iters))
        capacity = [ app_info[app_name]['capacity'][key] for key in sorted(app_info[app_name]["capacity"].keys())]
        print(capacity)
        for i in range(len(min_iters)):
            min_iters[i] += int(ratio*int(capacity[i]))
        print("min_iters2: {} {}".format(throughput_tmp, min_iters))
    if min_iters is not None:
        min_iters = [int(val)*50 for val in min_iters]
    return min_iters 

def system_control():
    # read container information    
    app_info, container_name_list, latency, throughput = helper.read_container_info()
  
    measured_cpu = helper.read_measured_data(app_info, container_name_list)
    # save cpu limit
    final_cpu_limit = []
    previous_cpu_limit = []
    # save all app's throughput, using throughput as the rank to decide final cpu usage. 
    all_app_throughput = []
    

    for key in sorted(app_info.keys()):
        print("***********************************************************************")
        app_name = key
        value = app_info[key]
        location = value["container_loc"]
        # real throughput
        current_throughput = app_info[app_name]["throughput"]
        all_app_throughput += current_throughput,
        if len(throughput[app_name]) > 0 and current_throughput < throughput[app_name][-1] and app_info[app_name]["latency"] > latency[app_name][-1]:
             current_throughput = throughput[app_name][-1]  
             app_info[app_name]["throughput"] = current_throughput

        opt = get_bo_model(app_name, current_throughput, len(location))    

        history_cpu = helper.read_history_data(app_name) 
        app_cpu_limit = history_cpu[-1].copy()    
        previous_cpu_limit += app_cpu_limit
 
        y = bo_function(app_info, app_name, app_cpu_limit)
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
 
        if len(res.func_vals) < 10  or (len(res.func_vals) < 15 and is_workload_changed(throughput[app_name])):
            print("start phase or workload changed")
            pass
        else:
            # check throughput
            # we should decrease CPU limit only if BO tells us to decrease it in two consecutive sampling intervals. Otherwise, we dont decrease. 
            if len(throughput[app_name]) > 3 and (throughput[app_name][-1] < throughput[app_name][-2]) and  abs(throughput[app_name][-1] - throughput[app_name][-2]) > 3000 and abs(throughput[app_name][-2] - throughput[app_name][-3]) < 2000:
                 min_iters = app_cpu_limit
            else:         
                #need to do optimization.
                # choose best from all case that don't violate SLO.
                min_iters = choose_best_from_model(res, app_name, app_info)
            print("find_best configure ", min_iters) 
        # first time to training model
        if min_iters:
            app_cpu_limit = min_iters 
            if app_info[app_name]["latency"] < helper.threshold[app_name] and sum(app_cpu_limit) > sum(history_cpu[-1]): 
                app_cpu_limit = history_cpu[-1].copy() 
            helper.write_best_configuration(app_name, current_throughput, app_cpu_limit)
        else: 
            app_cpu_limit = bo_model(key, app_info, app_cpu_limit, measured_cpu, container_name_list, latency[key], history_cpu) 
        print("app_cpu_limit {} {}".format(app_cpu_limit, history_cpu[-1]))
        final_cpu_limit += app_cpu_limit
        print('{} iteration: update cpu limit is {}'.format(key, final_cpu_limit))
        # todo, make sure the cpu limit shouldn't less than some value if we have low throughput model. 
        # Ex. since we allocate very small cpu limit, this cause the next throughput very low. Then, we will choose wrong model next time. We need to avoid this situation. 
    # using throughput as priority to decide normalized CPU usage.
    print('final cpu limit is {}'.format(final_cpu_limit))
    if sum(final_cpu_limit) > helper.QUOTA:
        priority_rank = []
        for value in sorted(all_app_throughput):
            for key in app_info.keys():
                if value == app_info[app_name]["throughput"]:
                    priority_rank += [app_name, value],
        for i in range(len(priority_rank)):
            key = priority_rank[i][0]
            loc = app_info[key]["container_loc"]
            for l in loc:
                # if we don't have enough CPU, give some app more weight to have a more cpu when we do normalization.
                if app_info[key]["latency"] > helper.threshold[app_name]:
                    final_cpu_limit[l] *= 1 + (len(priority_rank))*0.05 

        print('final cpu limit2 is {}'.format(final_cpu_limit))

        final_cpu_limit = helper.normalized(final_cpu_limit)
        print('final cpu limit2 is {}'.format(final_cpu_limit))


    for key in sorted(app_info.keys()):
        loc = app_info[key]["container_loc"]
        app_cpu_limit = [final_cpu_limit[l] for l in loc]
        helper.write_history_data(app_cpu_limit, key) 
            
    for i in range(len(previous_cpu_limit)):
        if previous_cpu_limit[i] != final_cpu_limit[i]:
            helper.change_cpu(container_name_list[i], final_cpu_limit[i]*100)
    
    helper.write_cpu_limit_file(final_cpu_limit)
 
    print("end this iteration\n\n")


start = timeit.default_timer()

system_control()

stop = timeit.default_timer()

print('Time: ', stop - start)  
