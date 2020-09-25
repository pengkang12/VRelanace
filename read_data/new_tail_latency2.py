#!/bin/python

import json
import requests
import sys
import os
import collections

file_dir=sys.argv[1]

ret = []
ret_through = []
sink_time = []
with open(file_dir+"/request-data.txt") as f:
    for line in f:
        if "latency_time" not in line:
            continue
        words = line.split(" ")
        sink_time.append(int(words[2])) 

sink = {}
with open(file_dir+"/sink0.txt") as f:
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
with open(file_dir + "/spout0.txt") as f:
    for line in f:
        words = line.split(',')
        spout[words[6]] = words[4]
result = []
latency_list1 = []
through_list1 = []
print(len(spout))
print(len(sink))
count = 0
for simple, keys in sink_bucket.items():
    for key in keys:
        if key in spout:
            result += (int(sink[key]) - int(spout[key])),
    if count == 5:
        count = 0
        if not result:
            end_to_end_latency = 0
            through_list1 += 0,
        else:     
            result.sort()
            through_list1 += len(result),
            end_to_end_latency=int(sum(result[:int(len(result)*0.95)])/(len(result)*0.95))
            print(simple, end_to_end_latency, len(result))
            result = []
        latency_list1 += end_to_end_latency,
             
    count += 1
    


sink1 = {}
with open(file_dir+"/sink1.txt") as f:
    for line in f:
        words = line.split(',')
        sink1[words[5]] = int(words[4])

sink_bucket = collections.OrderedDict(list())
for point in sink_time:
    if not point in sink_bucket:
        sink_bucket[point] = []
    for key, val in sink1.items():
        if point-10000 < val <= point:
            sink_bucket[point] += key, 

spout1 = {}
with open(file_dir + "/spout1.txt") as f:
    for line in f:
        words = line.split(',')
        spout1[words[6]] = words[4]
result = []
latency_list2 = []
through_list2 = []
count = 0
for simple, keys in sink_bucket.items():
    for key in keys:
        if key in spout1:
            result += (int(sink1[key]) - int(spout1[key])),

    if count == 5:
        count = 0
        if not result:
            end_to_end_latency = 0
        else:     
            result.sort()
            end_to_end_latency=int(sum(result[:int(len(result)*0.95)])/(len(result)*0.95))
            print(simple, end_to_end_latency, len(result))
        
        through_list2 += len(result),
        result = []
        latency_list2 += end_to_end_latency,
    count += 1

ret = [latency_list1[i] + latency_list2[i] for i in range(len(latency_list1))]
ret_throughput = [through_list1[i]+through_list2[i] for i in range(len(through_list1))]
print(latency_list1)
print(latency_list2)

print(ret)
print(ret_throughput)
