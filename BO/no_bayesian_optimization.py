#!/bin/python3

import numpy as np
import os
import sys
import json
import warnings
import timeit
if not sys.warnoptions:
    warnings.simplefilter("ignore")

threshold = {
    "ETLTopologySys": 100,
    "ETLTopologyTaxi": 100,
    "IoTPredictionTopologySYS" : 100,
    "IoTPredictionTopologyTAXI" : 100,
}
threshold_range = 25
QUOTA = 4000

app_name = threshold.keys()

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
    print(app_info)
    print(throughput)
    keys = {}
    return app_info, keys, latency, throughput


def system_control():
    # read container information    
    app_info, container_name_list, latency, throughput = read_container_info()
    print("end this iteration\n\n")


start = timeit.default_timer()

system_control()

stop = timeit.default_timer()

                                           
