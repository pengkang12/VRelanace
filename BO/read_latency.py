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
latency = {}
throughput = {}
cpu={}
measured_cpu={}
location = {}
input_filename = "/tmp/latency.log"
app_name = ['ETLTopologySys', "IoTPredictionTopologySYS"]

for name in app_name:
    latency[name] = []
    throughput[name] = []
    cpu[name] = []
    measured_cpu[name] = []
    location[name] = []
with open(input_filename) as f:
    for line in f:
        info = json.loads(line.replace("'", "\""))
        for name in app_name: 
            latency[name] += info[name]['latency'],
            throughput[name] += info[name]['throughput'],
            cpu[name] += info[name]['cpu_usage'],
            measured_cpu[name] += sum(info[name]['cpu_usage'].values()),
            location[name] = info[name]['container_loc']

for name in app_name:
    print("latency{0} = {1}\nthroughput{0} = {2}\nmeasured_cpu{0} = {3}".format(name,latency[name], throughput[name], measured_cpu[name]))

for name in app_name:
    cpu_limit = []
    with open("/tmp/bo_cpulimit.txt") as f:
        #find all cpu limit for each application
        for line in f:
            info = line.split(",")
            cpu_limit += [int(info[x]) for x in location[name]],
    print("cpu{} = {}".format(name, [sum(a) for a in cpu_limit][:-1]))
    for i, a in enumerate(list(zip(*cpu_limit))):
        print("container{}{} = {}".format(name,i+1, list(a)[:-1]))
