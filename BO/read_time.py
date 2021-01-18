import sys
import json
import warnings
import os
name=sys.argv[1]
app_num=int(sys.argv[2])
name = name + "app" + str(app_num)

os.system("grep Time {0}".format("control.log") + "| awk '{print $4}' > /tmp/time.log")
os.system("grep Time bo.log | awk '{print $2}' > /tmp/time_predict.log")
#3. read input data from file'
input_filename = "/tmp/time.log"
input_filename2 = "/tmp/time_predict.log"
res = []
with open(input_filename) as f:
    count = 1
    group = []
    for line in f:
        group +=int(float(line.rstrip())*100)/100,  
        if count%app_num == 0:
            res += max(group),
            group = []
        count += 1
print("measure{} =".format(name),res)

res = []
with open(input_filename2) as f:
    for line in f:
        res += int(float(line.rstrip())*100)/100,
print("predict{}=".format(name), res)


os.system("grep -A 1 'End' control.log > /tmp/process.log")
res_p = []
res_m = []
with open("/tmp/process.log") as f:
    count = 1
    count2 = 0
    for line in f:
        if count%3 == 2 and "start" not in line:
            #if count2%3 == 0:
            #    count2+=1
            #    count += 1
            #    continue
            count2 += 1
            tmp = line.rstrip().split(" ")
            res_p += int(tmp[0].rstrip("%")),
            res_m += int(int(tmp[1])/1000),
          
        count += 1
def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
res_p = list(map(sum, list(chunks(res_p, app_num))))
print("process_measure{} =".format(name), res_p)
res_m = list(map(sum, list(chunks(res_m, app_num))))
print("memory_measure{} =".format(name), res_m) 

os.system("grep -A 1 'Time' bo.log > /tmp/time_predict.log")
res_p = []
res_m = []
with open("/tmp/time_predict.log") as f:
    count = 1
    for line in f:
        if count%3 == 2:
            tmp = line.rstrip().split(" ")
            res_p += int(tmp[0].rstrip("%")),
            res_m += int(int(tmp[1])/1000),
        count += 1
print("memory_predict{} =".format(name), res_m)
print("process_predict{} =".format(name), res_p) 


