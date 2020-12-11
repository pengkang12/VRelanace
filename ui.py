#!/bin/python3
import requests
import sys
import time
import os
import json

app=sys.argv[1]

import redis

# step 2: define our connection information for Redis
# Replaces with your configuration information
redis_host = "master"
redis_port = 6379
redis_password = ""

bucket = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536]

def get_power(number):
     for i in range(16):
         if number < bucket[i]: 
             return i - 1
     return 16
     

def calculate_latency(appName="ETLTopologySys"):
    """calculate latency from Redis data
    https://blog.bramp.net/post/2018/01/16/measuring-percentile-latency/
    """
    throughput = 0 
    tail_latency = 0
    try:
        r = redis.StrictRedis(host=redis_host, port=redis_port, password=redis_password, decode_responses=True)
        msgs = []

        # calculate latency for 1 minute.
        timestamp = int(time.time() - 59)
        # for test 
        #timestamp = 1595026134
        #print(msgs_all)
        p = r.pipeline()
        for i in range(60):
            p.keys(appName+"_"+str(timestamp+i)+"*")
        results = p.execute()
        for result in results:
            msgs += result
        #print(msgs)
        #print("msg length is ", len(msgs))
        # use pipeline to improve redis effiency. 
        sink = r.hgetall(appName+"_sink")
        #latency = []
        latency_bucket = [ 0 for i in range(len(bucket))]
        tail_latency = 65536
        for i in range(len(msgs)):
            word = msgs[i].split("_") 
            if word[3] in sink:
                new_latency = int(sink[word[3]])-int(word[1])
                index = get_power(new_latency)
                latency_bucket[index] += 1 
                #latency += new_latency,
        #print(latency_bucket)
        latency_ratio = []
        count = 0
        throughput = sum(latency_bucket)
        for i in range(len(bucket)):
            count += latency_bucket[i]
            if throughput > 0:
                latency_ratio.append(count*1.0/throughput)
            else:
                latency_ratio.append(1)
        for i in range(len(bucket)):
            if latency_ratio[i] >= 0.95:
                break
 
        #print(i, bucket[i],bucket[i+1], latency_ratio[i-1], latency_ratio[i])
        if i >= 16:
            tail_latency = 65536
            if throughput == 0:
                tail_latency = 0
        else:
            tail_latency = bucket[i] + (bucket[i+1] - bucket[i])*(0.95 - latency_ratio[i-1])/(latency_ratio[i] - latency_ratio[i-1])
        #print(bucket)
        print(len(msgs), tail_latency)
        """ 
        if len(latency) > 0:
            latency = sorted(latency)
            tail_latency = latency[int(len(latency)*0.95)-2]
            print(len(msgs), len(latency), tail_latency, latency[int(len(latency)*0.9)])
         
     
        #delete redis data 
        timestamp -= 120
        msgs=[]
        for i in range(60):
            msgs += r.keys(appname+"_"+str(timestamp+i)+"*")
        p = r.pipeline()
          
        for msg in msgs:
            word = msg.split("_")
            p.hdel(appname+"_sink", word[3])
        p.delete(appName+"_sink")
        ret=p.execute()
        """ 
        keys = r.keys(appName+"_*")
        r.delete(*keys)

    except Exception as e:
        print(e)
    return tail_latency, throughput


url = "http://localhost:8080/api/v1/topology/"

def statistic_info(app_id):
    result = {}

    r = requests.get(url+app_id)
    data = r.json()
    #print(data)
    print("\nstart experiment------------------------------")
    total_execute = 0
    total_capacity = 0 
    bolts_capacity = {}
    for each in data['bolts']:
        # sink may influence our results. Therefore, we don't use sink as metrics.  
        if 'sink' in each['boltId']:
            continue
        total_capacity += float(each['capacity'])
        print("boltId {0} capacity {1}".format(each['boltId'], str(each['capacity'])))
        bolts_capacity[each['boltId']] = float(each['capacity'])
    #print("{0}".format(data['bolts']))
    #collect container cpu usage for each minute. we should calculate cpu usage, then run collect_container_cpu.py to produce new data for next minute. 
    cpu = {}
    count = 0
    with open("/tmp/kube-cpu.txt") as f:
        for line in f:
            if "CPU" in line:
                count += 1
            if "storm-worker" not in line:
                continue
            words = [word for word in line.split(" ") if word != None and word != ""]
            #cpu[words[0]] = cpu.get(words[0], 0) + int(words[1][:-1])
            if words[0] not in cpu:
                cpu[words[0]] = []
            cpu[words[0]] += int(words[1][:-1]),
   
    # calculate cpu usage for application's worker .
    app_cpu = {}
    capacity_ratio = {}
    for each in data['workers']:
        capacity = 0
        print("{0} {1}".format(each['host'], each['componentNumTasks']))
        for component in each['componentNumTasks'].keys():
            if component in bolts_capacity:
                capacity += bolts_capacity[component]
        if total_capacity == 0:
            return
        if capacity/total_capacity < 0.3:  
            capacity_ratio[each['host']] = 1 
        elif capacity/total_capacity < 0.6:  
            capacity_ratio[each['host']] = 1.3
        else:
            capacity_ratio[each['host']] = 1.6
        """ 
        if 'sink' in each['componentNumTasks']:
            os.system("echo {0} > /tmp/sink.name".format(each['host']))
        if 'spout1' in each['componentNumTasks'] or 'spout' in each['componentNumTasks']:
            os.system("echo {0} > /tmp/spout.name".format(each['host']))
        """
        #cpu[each['host']].sort()
        #print(cpu[each['host']])
        app_cpu[each['host']] = int(sum(cpu[each['host']])/len(cpu[each['host']]))
        #app_cpu[each['host']] = max(max(cpu[each['host']]), 100)
#
#[int(len(cpu[each['host']])*0.9)]

    print("The name of application is {0}, count is {1}".format(data['name'], count))
    #for key in app_cpu.keys():
    #     app_cpu[key] /=count
      
    result['latency'], result['throughput'] = calculate_latency(data['name'])
    result['cpu_usage'] = app_cpu
    result['capacity'] = capacity_ratio
 
    with open('/tmp/skopt_input_{0}.txt'.format(data['name']), 'a+') as f: 
        f.write(json.dumps(result)+"\n")
    print("result is ", result)
    """
    # testing data
    with open('/tmp/bo_search.log') as f: 
        for x in f:
            print(json.loads(x))
    """


    switch = False
    for each in data['topologyStats']:
        if each['window'] == "600":
            switch = True
            #print("window {0} emitted {1} transferred {2} acked {3}".format(each['window'], each['emitted'], each['transferred'], each['acked']))
    if switch== False:
        #print("window {0} emitted {1} transferred {2} acked {3}".format(600, 0, 0, 0))
        pass 
    for each in data['spouts']: 
        print("spouts emmited {0}".format(each['emitted']))
 
    print("{0} total capacity is {1}".format(app_id, total_capacity))

def getTopologySummary():
    r = requests.get(url+"summary")
    data = r.json()
    for each in data['topologies']:
        if app in each['id']:
            statistic_info(each['id'])
    print("end experiments")            

print("start program --------------------------")
import timeit

start = timeit.default_timer()


getTopologySummary()
#os.system("python BO/bayesian_optimization.py")
if app == "IoT":
    #os.system("python BO/bayesian_optimization.py >> /tmp/bo.log")
    pass

stop = timeit.default_timer()

print('End program Time: ', stop - start)  
