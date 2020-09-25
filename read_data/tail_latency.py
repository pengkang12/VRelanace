#!/bin/python
import os

sink = {}
last_word = None

#os.system('kubectl exec storm-worker-controller-qlgpp -- tail -n 1000 /tmp/riot-bench-output/spout-ETLTopology-sys-SYS-10000-0.01.log1651000000005 > /tmp/spout.txt')
#os.system('kubectl exec -it storm-worker-controller-ss26v -- tail -n 100 /tmp/riot-bench-output/sink-ETLTopology-sys-SYS-10000-0.01.log >> /tmp/sink.txt')

with open("/tmp/sink.txt") as f:
    for line in f:
        words = line.split(',')
        sink[words[5]] = words[4]
spout = {}
with open("/tmp/spout.txt") as f:
    for line in f:
        words = line.split(',')
        spout[words[6]] = words[4]

result = []
count = 1
print(len(spout))
print(len(sink))
for key, value in sink.items():
    if count == 1000:
        result.sort()
        print(result)
        end_to_end_latency=sum(result[:int(count*0.95)])/(count*0.95)
        print(end_to_end_latency, len(result))
        count = 0
        result = []   
    if key in spout:
        result.append(int(value) -int(spout[key]))
    count+=1
