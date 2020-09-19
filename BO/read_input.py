import json

input_filename = "/tmp/skopt_input_ETLTopologySys.txt"
a = []
throughput = []
d = []
c = []
with open(input_filename) as f:
    for line in f:
        app_info = json.loads(line)
        a.append(app_info['latency'])
        throughput.append(app_info['throughput'])
        d.append(app_info['cpu_usage'])
        c.append(sum(app_info['cpu_usage'].values()))

keys = d[1].keys() 
 
print(keys) 
         
print("latency = {}\nthroughput = {}\nmeasured_cpu = {}".format(a, throughput, c)) 
for i, a in enumerate(list(zip(*d))): 
    print("container{} = {}".format(i+1, list(a)))

