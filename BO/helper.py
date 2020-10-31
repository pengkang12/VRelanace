"""
reference: https://readthedocs.org/projects/mlrose/downloads/pdf/stable/
https://mlrose.readthedocs.io/en/stable/source/tutorial1.html#
https://www.cs.unm.edu/~neal.holts/dga/optimizationAlgorithms/hillclimber.html
"""
import mlrose 
import numpy as np
import os.path
from os import path
import time
import os
import sys
import json
import warnings
if not sys.warnoptions:
    warnings.simplefilter("ignore")


model_file = "/tmp/skopt_model_"
best_conf_file = "/tmp/bo_best_conf_"
cpu_limit_filename="/tmp/bo_cpulimit.txt"
history_cpu_filename="/tmp/bo_history_"
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
        t = int(v/50 + 0.5)*50
        if t >= QUOTA:
            t = QUOTA 
        if t <= 150:
            t = 150

        ret.append(t)
    return ret

def read_history_data(name):
    history_cpu = []
    with open(history_cpu_filename+name) as f1:
        line = None
        for line in f1:
            cpu = line.split(",")
            history_cpu.append([int(i) for i in cpu])
    # peng's method
    return history_cpu

def write_history_data(last_cpu_limit, name):
    with open(history_cpu_filename+name, 'a') as f2:
        f2.write(",".join([str(i) for i in last_cpu_limit])+"\n")


def read_measured_data(app_info, keys):
    history_cpu = []
    if os.path.exists(cpu_limit_filename) == False:
        cpu = []
        for key in threshold.keys():
            cpu += [400, 400, 400]
            write_history_data([400, 400, 400], key)
        history_cpu.append(cpu)
        write_cpu_limit_file(cpu)
    history_cpu = []
    with open(cpu_limit_filename) as f1:
        line = None
        for line in f1:
            cpu = line.split(",")
            history_cpu.append([int(i) for i in cpu])
    # peng's method
    measured = [] 
    for key in keys:
        for value in app_info.values():
            if key in value["cpu_usage"]:
                #measured.append(value['cpu_usage'][key]+50*value['capacity'][key])
                measured.append(value['cpu_usage'][key])
    #print("last cpu limit {}, measured cpu {}, ratio is {}".format(history_cpu, measured, sum(measured)/sum(history_cpu[-1])))
    return measured

def read_container_info():
    app_info = {}
    latency = {}
    throughput = {}
    for name in app_name:
        latency[name] = []
        throughput[name] = []
 
        input_filename = "/tmp/skopt_input_{}.txt".format(name)
        if os.path.exists(input_filename) == False:
            app_info[name] = {}
            continue
        with open(input_filename) as f:
            for line in f: 
                tmp_line = json.loads(line)
                latency[name] += tmp_line["latency"],
                throughput[name] += tmp_line["throughput"],
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
    print(throughput)
    return app_info, keys, latency, throughput

def write_cpu_limit_file(last_cpu_limit):
    mode = 'a'
    # if os.path.exists(cpu_limit_filename) else 'w'
    with open(cpu_limit_filename, mode) as f2:
        f2.write(",".join([str(i) for i in last_cpu_limit])+"\n")

def read_best_configuration(app_name, throughput, length):
    if os.path.exists(best_conf_file+app_name) == False:
        with open(best_conf_file+app_name, "w+") as f:
            pass

    ret = None
    with open(best_conf_file+app_name) as f:
        for line in f:
            word = line.split(",") 
            if length + 1 == len(word) and int(word[0]) > throughput*0.9 and int(word[0]) < throughput*1.25:
                return [ int(val) for val in word[1:]] 
    return ret

def write_best_configuration(app_name, throughput, conf):
    ret = None
    with open(best_conf_file+app_name, "a") as f:
        f.write("{},{}\n".format(str(throughput), ",".join([str(val) for val in conf])))
    with open(history_cpu_filename+app_name, "w+") as f:
        pass
    #if os.path.exists(model_file+app_name) == True:
    #    os.system("rm {}".format(model_file+app_name))

def write_window_file(current_window, window, filename):
    with open("/tmp/window_{}.txt".format(filename), "w") as f1:
        f1.write("{},{}".format(str(current_window), str(window)))
 
def read_window_file(filename):
    current_window = 0
    window = 10

    line = None 
    with open("/tmp/window_{}.txt".format(filename)) as f1:
        for line in f1: 
            current_window, window = line.split(",") 
    if line == None:
        write_window_file(current_window, window, filename)     
    return int(current_window), int(window)
