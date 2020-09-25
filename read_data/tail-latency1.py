#!/bin/python

import json
import requests
import sys
import os
import collections

file_dir=sys.argv[1]

name=sys.argv[2]


ret = []
throughput = []

sink_time = []
with open(file_dir+"/request-data.txt") as f:
    for line in f:
        if "latency_time" not in line:
            continue
        words = line.split(" ")
        sink_time.append(int(words[2])) 

sink = {}
with open(file_dir+"/sink{0}.txt".format(name)) as f:
    for line in f:
        words = line.split(',')
        sink[words[1]] = int(words[0])

sink_bucket = collections.OrderedDict(list())
previous=sink_time[0]-60000
for i in range(len(sink_time)):
    point = previous + 60000
    #point = sink_time[i]
    if not point in sink_bucket:
        sink_bucket[point] = []
    for key, val in sink.items():
        if previous < val <= point:
            sink_bucket[point] += key, 
    previous = point

spout = {}
with open(file_dir + "/spout{0}.txt".format(name)) as f:
    for line in f:
        words = line.split(',')
        spout[words[2]] = words[0]
result = []
latency_list2 = []
count = 0
for simple, keys in sink_bucket.items():
    for key in keys:
        if key in spout:
            result += (int(sink[key]) - int(spout[key])),
    if count == 1:
        count = 0
        if not result:
            end_to_end_latency = 0
        else:     
            result.sort()
            #end_to_end_latency=int(sum(result[:int(len(result)*0.95)])/(len(result)*0.95))
            end_to_end_latency=result[int(len(result)*0.95)-1]
            cdf = [ result[int(len(result)*i/20)-1] for i in range(1, 20)]
            print(len(result), cdf)
        throughput += len(result),
        latency_list2 += end_to_end_latency,
        result = [] 
    count += 1

ret = latency_list2

print(ret)
print(len(ret))
print(throughput)
print(len(throughput))
