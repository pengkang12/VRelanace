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


def calculate_latency(appName="ETLTopologySys"):
    """calculate latency from Redis data"""
    latency = [0] 
    try:
        r = redis.StrictRedis(host=redis_host, port=redis_port, password=redis_password, decode_responses=True)
        msgs = []

        # calculate latency for 1 minute.
        timestamp = int(time.time() - 59)
        # for test 
        #timestamp = 1595026134
        #print(msgs_all)
        for i in range(60):
            msgs += r.keys(appName+"_"+str(timestamp+i)+"*_MSGID_*")
        #print("msg length is ", len(msgs))
        # use pipeline to improve redis effiency. 
        sink = r.hgetall(appName+"_sink")
        latency = [] 
        tail_latency = -1
        for i in range(len(msgs)):
            word = msgs[i].split("_") 
            if word[3] in sink:
                latency += int(sink[word[3]])-int(word[1]),     
        if len(latency) > 0:
            latency = sorted(latency)
            tail_latency = latency[int(len(latency)*0.9)]
            print(len(msgs), len(latency), tail_latency, latency[int(len(latency)*0.95)-1])
        # delete old data before 10 mins
        timestamp -= 180
        msgs=[]
        for i in range(60):
            msgs += r.keys(appName+"_"+str(timestamp+i)+"*_MSGID_*")
        p = r.pipeline()
        for msg in msgs:
            word = msg.split("_")
            p.hdel(appName+"_sink", word[3])
            p.delete(msg)
        ret=p.execute()
        print("delete old message",len(msgs), len(ret)) 
    except Exception as e:
        print(e)
    return tail_latency, len(latency)


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
   

    os.system("python collect_container_cpu.py &")
   
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
            capacity_ratio[each['host']] = 1.5 
        else:
            capacity_ratio[each['host']] = 2
        """ 
        if 'sink' in each['componentNumTasks']:
            os.system("echo {0} > /tmp/sink.name".format(each['host']))
        if 'spout1' in each['componentNumTasks'] or 'spout' in each['componentNumTasks']:
            os.system("echo {0} > /tmp/spout.name".format(each['host']))
        """
        #cpu[each['host']].sort()
        print(cpu[each['host']])
        app_cpu[each['host']] = max(cpu[each['host']])
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
getTopologySummary()
#os.system("python BO/bayesian_optimization.py")
os.system("python BO/bayesian_optimization.py >> /tmp/bo.log")
