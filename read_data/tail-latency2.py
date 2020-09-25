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
with open(file_dir+"/sinkETL0.txt") as f:
    for line in f:
        words = line.split(',')
        sink[words[1]] = int(words[0])



sink_bucket = collections.OrderedDict(list())

previous=sink_time[0]-60000
for i in range(len(sink_time)):
    point = sink_time[i]
    if not point in sink_bucket:
        sink_bucket[point] = []
    for key, val in sink.items():
        if previous < val <= point:
            sink_bucket[point] += key,
    previous = point

spout = {}
with open(file_dir + "/spoutETL0.txt") as f:
    for line in f:
        words = line.split(',')
        spout[words[2]] = words[0]
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
    if count == 1:
        count = 0
        end_to_end_latency = 0
        if len(result)>0:
            result.sort()
            #print(simple, end_to_end_latency, len(result))
            end_to_end_latency=result[int(len(result)*0.95)-1]
            cdf = [ result[int(len(result)*i/20)-1] for i in range(1, 20)]
            print(len(result), cdf)

        through_list1 += len(result),
        latency_list1 += end_to_end_latency,
        result = []

    count += 1
    


sink1 = {}
with open(file_dir+"/sinkETL.txt") as f:
    for line in f:
        words = line.split(',')
        sink1[words[1]] = int(words[0])

sink_bucket = collections.OrderedDict(list())
previous=sink_time[0]-60000
for i in range(len(sink_time)):
    point = sink_time[i]
    if not point in sink_bucket:
        sink_bucket[point] = []
    for key, val in sink1.items():
        if previous < val <= point:
            sink_bucket[point] += key,
    previous = point

spout1 = {}
with open(file_dir + "/spoutETL.txt") as f:
    for line in f:
        words = line.split(',')
        spout1[words[2]] = words[0]
result = []
latency_list2 = []
through_list2 = []
count = 0
for simple, keys in sink_bucket.items():
    for key in keys:
        if key in spout1:
            result += (int(sink1[key]) - int(spout1[key])),

    if count == 1:
        count = 0
        
        end_to_end_latency = 0
        if len(result) > 0:
            result.sort()
            #print(simple, end_to_end_latency, len(result))
            end_to_end_latency=result[int(len(result)*0.95)-1]
            cdf = [ result[int(len(result)*i/20)-1] for i in range(1, 20)]
            print(len(result), cdf)
        
        through_list2 += len(result),
        result = []
        latency_list2 += end_to_end_latency,
    count += 1

ret = [latency_list1[i] + latency_list2[i] for i in range(len(latency_list1))]
ret_throughput = [through_list1[i]+through_list2[i] for i in range(len(through_list1))]
print(latency_list1)
print(latency_list2)

print(ret)
print(len(ret))
print(ret_throughput)
print(len(ret_throughput))
