"""
reference: https://readthedocs.org/projects/mlrose/downloads/pdf/stable/
https://mlrose.readthedocs.io/en/stable/source/tutorial1.html#
https://www.cs.unm.edu/~neal.holts/dga/optimizationAlgorithms/hillclimber.html
"""
import mlrose 
import numpy as np

import time
import os
import sys
import json
import warnings
if not sys.warnoptions:
    warnings.simplefilter("ignore")

cpu_limit_filename="/tmp/bo_cpulimit.txt"
model_filename = "/tmp/skopt.model"
threshold = {
    "ETLTopologySys": 100,
    "IoTPredictionTopologySYS" : 100, 
}
threshold_range = 25
QUOTA = 4000

app_name = threshold.keys()

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
        total += 50*len(a)
        a = [int((QUOTA/total)*val) for val in a]
        print(sum(a)) 
    for v in a:
        t = int(v/50 + 1)*50
        if t >= QUOTA:
            t = QUOTA 
        if t <= 100:
            t = 100

        ret.append(t)
    return ret

def read_measured_data(app_info, keys):
    history_cpu = []
    with open(cpu_limit_filename) as f1:
        line = None
        for line in f1:
            cpu = line.split(",")
            history_cpu.append([int(i) for i in cpu])
    if len(history_cpu) == 0:
        cpu = []
        for i in range(len(app_name)):
            for j in range(3):
                cpu += 400,
        history_cpu.append(cpu)
        write_cpu_limit_file(cpu)

    # peng's method
    measured = [] 
    for key in keys:
        for value in app_info.values():
            if key in value["cpu_usage"]:
                #measured.append(value['cpu_usage'][key]+50*value['capacity'][key])
                measured.append(value['cpu_usage'][key])
    print("last cpu limit {}, measured cpu {}, ratio is {}".format(history_cpu, measured, sum(measured)/sum(history_cpu[-1])))
    return history_cpu, measured

def read_container_info():
    app_info = {}
    latency = {}
    for name in app_name:
        latency[name] = []
        input_filename = "/tmp/skopt_input_{}.txt".format(name)
        with open(input_filename) as f:
            for line in f: 
                latency[name] += json.loads(line)["latency"],
                pass
            app_info[name] = json.loads(line)

    # we use lexical sort for container. 
    keys = []
    loc  = 0
    for key in sorted(app_info.keys()):
        value = app_info[key]
        location = []
        for key1 in sorted(value["cpu_usage"].keys()):
            keys.append(key1)
            location += loc,
            loc += 1
        app_info[key]["container_loc"] = location
    print(app_info)
    print(keys)
    return app_info, keys, latency

def write_cpu_limit_file(last_cpu_limit):
    with open(cpu_limit_filename, "a") as f2:
        f2.write(",".join([str(i) for i in last_cpu_limit])+"\n")

