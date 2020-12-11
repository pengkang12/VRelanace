

from skopt import gp_minimize
from skopt import Optimizer
import skopt.utils as skopt_utils
import numpy as np

import helper

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
app_name = helper.threshold.keys()

for name in app_name:
    latency[name] = []
    throughput[name] = []
    cpu[name] = []
    measured_cpu[name] = []
    location[name] = []
with open(input_filename) as f:
    for line in f:
        try:
            info = json.loads(line.replace("'", "\""))
        except:
            continue
        for name in app_name: 
            throughput[name] += info[name]['throughput'],
            if info[name]["throughput"] == 0:
                latency[name] += int(1),
            else:
                latency[name] += int(info[name]['latency']),
            cpu[name] += info[name]['cpu_usage'],
            measured_cpu[name] += sum(info[name]['cpu_usage'].values()),

for name in app_name:
    print("latency{0} = {1}\nthroughput{0} = {2}\nmeasured_cpu{0} = {3}".format(name,latency[name], throughput[name], measured_cpu[name]))
print("#*************************************************************************************************************")


