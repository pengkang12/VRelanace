kubectl delete -f ~/storm-peng/kube-storm/storm-worker-controller.json
sleep 30
kubectl cordon kube-slave2
sleep 15
kubectl create -f ~/storm-peng/kube-storm/storm-worker-controller.json
sleep 60
#kubectl uncordon kube-slave2
sleep 30
bash ~/storm-peng/kube-storm/change_worker_hosts.sh

kubectl exec nimbus -- /opt/apache-storm/bin/storm kill ETLTopologyTaxi
kubectl exec nimbus -- /opt/apache-storm/bin/storm kill ETLTopologySys
kubectl exec nimbus -- /opt/apache-storm/bin/storm kill IoTPredictionTopologySYS
kubectl exec nimbus -- /opt/apache-storm/bin/storm kill IoTPredictionTopologyTAXI
sleep 30
kubectl exec nimbus -- /bin/bash /opt/apache-storm/riot-bench/scripts/run_ETL_sys.sh 0.1
kubectl exec nimbus -- /opt/apache-storm/bin/storm rebalance ETLTopologySys -n 2

kubectl exec nimbus -- /bin/bash /opt/apache-storm/riot-bench/scripts/run_PREDICT_sys.sh 0.08
kubectl exec nimbus -- /bin/bash /opt/apache-storm/riot-bench/scripts/run_PREDICT_taxi.sh 0.01

sleep 120

#4
delay="600"
scale=0.01
fileDir="test_redis_latency"+$scale
#kubectl exec nimbus -- /bin/bash /opt/apache-storm/riot-bench/scripts/run_ETL_sys.sh $scale Stable
kubectl exec nimbus -- /bin/bash /opt/apache-storm/riot-bench/scripts/run_ETL_taxi.sh $scale Dynamic
kubectl exec nimbus -- /opt/apache-storm/bin/storm rebalance ETLTopologySys -n 3

sleep 120
#sleep $delay 
#sleep $delay 
#
# for bayasian optimization
bash schedule_control.sh > data/control_${scale}.log &
# for hill climb algorithm
#bash schedule_hillclimb.sh > data/contro_hillclimb_${scale}.log &
#bash schedule_rebalance.sh > data/control_${scale}_rebalance.log &

exit

bash test.sh $scale $fileDir & 

sleep $delay 
sleep $delay 
sleep $delay 

#python3 copy_message.py ETL 
#bash copy_latency.sh ETL data/${fileDir}/

#11kubectl exec nimbus -- /bin/bash /opt/apache-storm/riot-bench/scripts/run_PREDICT_sys.sh 0.02

echo "create predict"
#name=`kubectl get pod | grep storm-worker | awk '{print $1}'`
#ssh -tt kube-slave1 "echo syscloud | sudo -S bash cpu.sh ${name} 100000"
#kubectl exec nimbus -- /opt/apache-storm/bin/storm rebalance ETLTopology-sys -n 6

sleep $delay 
# stats is 1. 
#11kubectl exec nimbus -- /bin/bash /opt/apache-storm/riot-bench/scripts/run_STATS_sys.sh

sleep $delay 
sleep $delay 
#
#
echo "create stats"
echo "end"
sleep 60

python3 copy_message.py ETL 
#11python3 copy_message.py Predict
#11python3 copy_message.py Stats 

sleep 10
#kubectl exec nimbus -- /opt/apache-storm/bin/storm kill Stats_SQL_Topology_SYS
sleep 10
#kubectl exec nimbus -- /opt/apache-storm/bin/storm kill IoTPredictionTopologySYS

sleep 150

bash copy_latency.sh ETL data/${fileDir}/
sleep 10
#bash copy_latency.sh Predict data/${fileDir}/
sleep 10
#bash copy_latency.sh Stats data/${fileDir}/


exit

kubectl delete -f ~/storm-peng/kube-storm/storm-worker3-controller.json
sleep 15
kubectl cordon kube-slave2
sleep 15
kubectl create -f ~/storm-peng/kube-storm/storm-worker5-controller.json
sleep 10
kubectl uncordon kube-slave2

sleep 10

#4
kubectl exec nimbus -- /bin/bash /opt/apache-storm/riot-bench/scripts/run_ETL_sys.sh 0.01

sleep 20

kubectl exec nimbus -- /opt/apache-storm/bin/storm rebalance ETLTopology-sys -n 5


bash test.sh 0.01 virtual_rebalance_5worker1Container2 & 

sleep 1200
name=`kubectl get pod | grep storm-worker | awk '{print $1}'`
ssh -tt kube-slave1 "echo syscloud | sudo -S bash cpu.sh ${name} 120000"

sleep 1800


