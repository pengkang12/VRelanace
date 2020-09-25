#!/bin/python3
import requests
import sys
import os 

filename=sys.argv[1]

lines = []

os.system("grep 'window 600' {0} > tmp.txt".format(filename))
with open('tmp.txt') as f:
    for line in f: 
        words = line.split(" ")
        lines.append(int(words[3])) #storing everything in memory!

print("throughput_{0}_mem{1}={2}".format(sys.argv[2], sys.argv[3], lines))
print(len(lines))

lines = []
os.system("grep 'total execute time' {0} > tmp.txt".format(filename))
with open('tmp.txt') as f:
    for line in f: 
        words = line.split(" ")
        lines.append(float(words[5])) #storing everything in memory!

print("latency_{0}_mem{1}={2}".format(sys.argv[2], sys.argv[3], lines))
print(len(lines))


