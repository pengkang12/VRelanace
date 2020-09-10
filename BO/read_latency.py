from skopt import gp_minimize
from skopt import Optimizer
import skopt.utils as skopt_utils
import numpy as np

import os
import sys
import json
import warnings

os.system("grep \"latency'\" /tmp/bo.log > /tmp/latency.log")

#3. read input data from file'
a = []
throughput = []
c=[]
d=[]
input_filename = "/tmp/latency.log"
with open(input_filename) as f:
    for line in f:
        app_info = json.loads(line.replace("'", "\""))
        
        a.append(app_info['ETLTopologySys']['latency']) 
        throughput.append(app_info['ETLTopologySys']['throughput']) 
        d.append(app_info['ETLTopologySys']['cpu_usage'])
        c.append(sum(app_info['ETLTopologySys']['cpu_usage'].values())) 
print(d)
keys = d[1].keys()

for key in keys:
    temp = [x[key] for x in d]
    print(temp)
        
with open("/tmp/bo_cpulimit.txt") as f:
    d = []
    for line in f:
        app_info = line.split(",")
        d.append([int(x) for x in app_info])
print("latency = {}\nthroughput = {}\nmeasured_cpu = {}".format(a, throughput, c))
print("cpu = {}".format([sum(a) for a in d]))
for i, a in enumerate(list(zip(*d))):
    print("container{} = {}".format(i+1, list(a)))
