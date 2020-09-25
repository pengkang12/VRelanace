"""
reference: https://readthedocs.org/projects/mlrose/downloads/pdf/stable/
https://mlrose.readthedocs.io/en/stable/source/tutorial1.html#
https://www.cs.unm.edu/~neal.holts/dga/optimizationAlgorithms/hillclimber.html
"""
import numpy as np

import time
import os
import sys
import json
import warnings
if not sys.warnoptions:
    warnings.simplefilter("ignore")

import helper


app_info, keys = helper.read_container_info()
last_cpu_limit, measured = helper.read_measured_data(app_info, keys)


ret_y = 0
for key, value in app_info.items():
    if value["latency"] - helper.threshold[key] >0:
        ret_y += value["latency"] - helper.threshold[key] 

if ret_y > 0:
    #increase cpu
    for key, value in app_info.items():
        if value['latency'] - helper.threshold[key] > 0:
            location = value["container_loc"]
            max_ratio = max([measured[loc]/last_cpu_limit[loc] for loc in location])
            for loc in location:
                if abs(measured[loc]/last_cpu_limit[loc] - max_ratio) <= 0.01:
                    break
            last_cpu_limit[loc] += 50
            print("increase CPU since violation tail-latency")
            helper.change_cpu(keys[loc], last_cpu_limit[loc]*100)
            print("new cpu limit ", last_cpu_limit)
else:
    #decrease cpu
    print("try to decrease CPU to minimize CPU limit")
    if sum(measured)/sum(last_cpu_limit)< 0.8:

        min_ratio = min([measured[i]-last_cpu_limit[i] for i in range(len(last_cpu_limit))])
        for i in range(len(last_cpu_limit)):
            if (measured[i]-last_cpu_limit[i] ) == min_ratio:
                break
        last_cpu_limit[i] -= 50
        helper.change_cpu(keys[i], last_cpu_limit[i]*100)
        print("new cpu limit ", last_cpu_limit)
    else:
        print("find local best optimal point")
helper.write_cpu_limit_file(last_cpu_limit)
