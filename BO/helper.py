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
input_app_name = "/tmp/skopt_app_name.txt"
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

def read_measured_data(app_info, keys):
    with open(cpu_limit_filename) as f1:
        line = None
        for line in f1:
            pass
        cpu = []
        if line is None:
            for i in range(len(app_name)):
                for j in range(3):
                    cpu += 400,
        else:
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

def write_cpu_limit_file(last_cpu_limit):
    with open(cpu_limit_filename, "a") as f2:
        f2.write(",".join([str(i) for i in last_cpu_limit])+"\n")

