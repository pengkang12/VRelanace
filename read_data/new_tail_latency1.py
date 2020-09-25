#!/bin/python

import json
import requests
import sys
import os
import collections

file_dir=sys.argv[1]

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
with open(file_dir+"/sink1.txt") as f:
    for line in f:
        words = line.split(',')
        sink[words[5]] = int(words[4])

sink_bucket = collections.OrderedDict(list())
for point in sink_time:
    if not point in sink_bucket:
        sink_bucket[point] = []
    for key, val in sink.items():
        if point-10000 < val <= point:
            sink_bucket[point] += key, 

spout = {}
with open(file_dir + "/spout1.txt") as f:
    for line in f:
        words = line.split(',')
        spout[words[6]] = words[4]
result = []
latency_list2 = []
count = 0
for simple, keys in sink_bucket.items():
    for key in keys:
        if key in spout:
            result += (int(sink[key]) - int(spout[key])),
    if count == 5:
        count = 0
        if not result:
            end_to_end_latency = 0
        else:     
            result.sort()
            end_to_end_latency=int(sum(result[:int(len(result)*0.95)])/(len(result)*0.95))
            print(simple, end_to_end_latency, len(result))
        
        throughput += len(result),
        latency_list2 += end_to_end_latency,
        result = [] 
    count += 1

ret = latency_list2

print(ret)
print(throughput)

