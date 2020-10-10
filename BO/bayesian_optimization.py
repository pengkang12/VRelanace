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
QUOTA = 4000
noise_level = 0.1

def bo_function(app_info, app_name, app_cpu_limit):
    t = [] # measured tail latency 
    throughput = []
    motivation = [] # we need to allocate more cpu or less cpu for different application.
    #use x to update the container, and read new tail latency. 
    ret_y = app_info[app_name]["latency"] - helper.threshold[app_name]
    
    is_violate_target = False
    
    #return ret_y, is_violate_target
    if ret_y > 0:
        # violate target
        ret_val = max(0, ret_y)+ sum(app_cpu_limit)/QUOTA 
    else:
        ret_val = -1 * ret_y * sum(app_cpu_limit)/QUOTA 
    
    #ret_val = max(0, ret_y)+ sum(cpu_limit)/QUOTA 
    return ret_val, is_violate_target
 

def ask_model(opt, capacity, history_cpu, history_latency, location):
    suggested = []
    count = 0
    while count < 5:

        count += 1
        suggested = opt.ask(strategy='cl_min')
        break
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

def get_bo_model(app_name):
    model_file = model_filename+app_name
 
    if os.path.exists(model_file) == False:
        restriction=[]
        for j in range(3):
            restriction += [(100, QUOTA)]
        #opt = Optimizer(restriction, n_initial_points=2, acq_func="gp_hedge", base_estimator="GP")
        kernels = [1.0 * RBF(length_scale=1.0, length_scale_bounds=(1e-1, 10.0)),
           1.0 * RationalQuadratic(length_scale=1.0, alpha=0.1),
           1.0 * ExpSineSquared(length_scale=1.0, periodicity=3.0,
                                length_scale_bounds=(0.1, 10.0),
                                periodicity_bounds=(1.0, 10.0)),
           ConstantKernel(0.1, (0.01, 10.0))
               * (DotProduct(sigma_0=1.0, sigma_0_bounds=(0.1, 10.0)) ** 2),
           1.0 * Matern(length_scale=1.0, length_scale_bounds=(1e-1, 10.0),
                        nu=2.5)]
     
        gpr = GaussianProcessRegressor(kernel=kernels[0], alpha=noise_level ** 2,
                                   normalize_y=True, noise="gaussian",
                                   n_restarts_optimizer=2
                                   )
    
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
    opt = get_bo_model(app_name)    
 
    y, is_violate_target= bo_function(app_info, app_name, app_cpu_limit)
    location = app_info[app_name]["container_loc"]
 
    res  = opt.tell(app_cpu_limit, y)

    if len(history_cpu) >= 5:
        next_x = app_cpu_limit 
        # acquisition 
        #print("acquisition function ------", res)    
        x_gp = res.x_iters
        gp = res.models[-1]
        curr_x_iters = res.x_iters
        curr_func_vals = res.func_vals
    
        acq = acquisition.gaussian_ei(curr_x_iters, gp, y_opt=np.min(curr_func_vals))
     
        print("acquisition function ", acq)    

        # print("xgp and x_iters, ", x_gp, curr_x_iters)
        next_acq = acquisition.gaussian_ei(res.space.transform([next_x]), gp, y_opt=np.min(curr_func_vals))
        print("next acquistion function ", next_acq)

    if is_violate_target == True:
       # save the model
        suggest = ask_model(opt, app_info[app_name]['capacity'], history_cpu, latency, location)

        suggest = helper.normalized(suggest)
        print("normalized ", suggest)      
        #suggest = check_history_cpu_limit(history_cpu, suggest, latency, location, app_name)
        print("check hisotry ", suggest, app_cpu_limit)		
        for i in range(len(app_cpu_limit)):
            if int(suggest[i]) != app_cpu_limit[i]:
                app_cpu_limit[i] = int(suggest[i])
    skopt_utils.dump(opt, model_filename+app_name)
    print("-----------------------------------------------------------------") 
    return app_cpu_limit

def find_min_index(arr1, location, latency, throughput ):
    # we also need to choose maximum throughput
    max_throughput = max(throughput)*0.7
    bad_arr1 = []
    for i in range(len(arr1)):
        if latency[i] > 100:
            bad_arr1 += arr1[i],
    min_i = -1
    min_sum = helper.QUOTA
    for i in range(len(arr1)):
        tmp_sum = sum([arr1[i][loc] for loc in location])
        if tmp_sum < min_sum and latency[i] < 100 and arr1[i] not in bad_arr1 and throughput[i] >= max_throughput:
            print("choose min index ", tmp_sum, i, arr1[i])
            min_i = i
            min_sum = tmp_sum
    
    print(arr1[min_i], bad_arr1, max_throughput)  
    return min_i 

def system_control():
    # read container information    
    app_info, container_name_list, latency, throughput = helper.read_container_info()
  
    history_cpu, measured_cpu = helper.read_measured_data(app_info, container_name_list)
    
    cpu_limit = history_cpu[-1].copy()    
    print('iteration: measured is {}, last cpu limit is {}'.format(measured_cpu, cpu_limit))
    # save cpu limit
    final_cpu_limit = []
    for key in sorted(app_info.keys()):
        app_name = key
        current_window, window = helper.read_window_file(key)
        helper.write_window_file(current_window+1, window, key)


        if len(latency[key]) > 2 and latency[key][-2] > 100 and latency[key][-1] > 100 and current_window > 10:
            helper.write_window_file(0, 5, key)
            print("new write thing")
            current_window = 0
            os.system("rm {}{}".format(model_filename, key))

        value = app_info[key]
        location = value["container_loc"]
        app_cpu_limit = [cpu_limit[loc] for loc in location]

        # use logistic regression to decide whether we need to update Bayasian optimization model.
        logreg = logistic_regression.get_model(key)
        
        update_model = None
        try:
            X = [[app_info[app_name]["throughput"], sum(app_cpu_limit), min(app_cpu_limit), 3]]
            update_model = logreg.predict(X)
            print("logistic regression result is ", update_model)
            print("coef is {}, intercept is {}, decision function is {}, preidct_proba is {}".format(logreg.coef_, logreg.intercept_, logreg.decision_function(X), logreg.predict_proba(X) ))
        except:
            print("First time ")
       
        #if True or int(current_window) <= int(window):
        if update_model == None or update_model == 0: 
            X = [[app_info[app_name]["throughput"], sum(app_cpu_limit),min(app_cpu_limit), 3],[app_info[app_name]["throughput"], QUOTA,QUOTA, 3]]
            y = [0, 1]
            X_train = np.reshape(X, (len(X), len(X[0])))
            logreg.fit(X, y)    

            app_cpu_limit = bo_model(key, app_info, app_cpu_limit, measured_cpu, container_name_list, latency[key], history_cpu) 
            # normalize again for cpu limit
            #if sum(cpu_limit) > helper.QUOTA:
            #    cpu_limit = helper.normalized(cpu_limit)      
            #    pass
            final_cpu_limit += app_cpu_limit
            print('{} iteration: update cpu limit is {}'.format(key, cpu_limit))
        else:
            X = [[app_info[app_name]["throughput"], 300, 100, 3],
                 [app_info[app_name]["throughput"], sum(app_cpu_limit),min(app_cpu_limit), 3]
            ]
            y = [1, 0]
            logreg.fit(X, y)    

            history_cpu = history_cpu[-window:]
            #for key in sorted(app_info.keys()):
            latency_app = latency[key][-window:]
            throughput_app = throughput[key][-window:]
            index = find_min_index(history_cpu, location, latency_app, throughput_app)
            final_cpu_limit += [history_cpu[index][loc] for loc in location]
            print("{} this is find optimal value {}, {}".format(key, cpu_limit, history_cpu[-1]))

    logistic_regression.save_model(logreg, app_name)
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
