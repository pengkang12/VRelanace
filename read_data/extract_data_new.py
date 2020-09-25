import json
import requests
import sys
import os

filename=sys.argv[1]

sink = []
with open(filename) as f:
    for line in f:
        if "encodedBoltId" not in line:
            continue
        words = line.replace("'", '"')
        words = words.replace("True", '1')
        words = words.replace("False", '0')
        words = words.replace("None", '""')
        raw_data = json.loads(words)
        #print(raw_data['bolts'])
        for i in range(len(raw_data['bolts'])):
            bolt = raw_data['bolts'][i]
            if bolt['boltId'] == "sink":
                sink.append(bolt['executed'])
                #print(bolt['executed'])
average_sink = []

for i in range(1, len(sink)):
    if sink[i] - sink[i-1] > 0:
        average_sink.append(sink[i]-sink[i-1])
    elif sink[i] - sink[i-1] <= 0:
        average_sink.append(0)
print(len(average_sink))
print([0]+average_sink)
# Output: {'name': 'Bob', 'languages': ['English', 'Fench']}
