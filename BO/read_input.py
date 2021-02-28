import json

input_filename = "/tmp/skopt_input_ETLTopologySys.txt"
a = []
throughput = []
d = []
c = []
memory = []
with open(input_filename) as f:
    for line in f:
        app_info = json.loads(line)
        a.append(app_info['latency'])
        throughput.append(app_info['throughput'])
        d.append(app_info['cpu_usage'])
        c.append(sum(app_info['cpu_usage'].values()))
        memory += sum(app_info['memory_usage'].values()),
keys = d[1].keys() 
 
print(keys) 
         
print("latency = {}\nthroughput = {}\nmeasured_cpu = {}\nmeasured_memory = {}".format(a, throughput, c, memory)) 
#for i, a in enumerate(list(zip(*d))): 
#    print("container{} = {}".format(i+1, list(a)))

