import sys
import json
import warnings
import os

os.system("grep Time data/control_0.01.log | awk '{print $4}' > /tmp/time.log")
os.system("grep Time /tmp/bo.log | awk '{print $2}' > /tmp/time_predict.log")
#3. read input data from file'
input_filename = "/tmp/time.log"
input_filename2 = "/tmp/time_predict.log"
res = []
with open(input_filename) as f:
    count = 1
    for line in f:
        if count%4 == 0:
            res += int(float(line.rstrip())*100)/100,
        count += 1
print(res)

res = []
with open(input_filename2) as f:
    for line in f:
        res += int(float(line.rstrip())*100)/100,
print(res)
