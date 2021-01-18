rm /tmp/skopt_input_ETLTopologySys.txt


bash script/redis-data.sh


python collect_container_cpu.py &
sleep 120
for i in {1..11}
do
python collect_container_cpu.py &
python ui.py ETLTopologySys &
python ui.py IoTPredictionTopologySYS &
sleep 120
done

kubectl exec nimbus -- /opt/apache-storm/bin/storm rebalance ETLTopologySys -n 5 -e BloomFilterBolt=2 -e InterpolationBolt=2 -e JoinBolt=2 -e RangeFilterBolt=2 -e SenMlParseBolt=2

for i in {1..11}
do
python collect_container_cpu.py &
python ui.py ETLTopologySys &
python ui.py IoTPredictionTopologySYS &
sleep 120
done

kubectl exec nimbus -- /opt/apache-storm/bin/storm rebalance ETLTopologySys -n 6 #-e BloomFilterBolt=4 -e InterpolationBolt=4 -e JoinBolt=4 -e RangeFilterBolt=4 -e SenMlParseBolt=4

for i in {1..12}
do
python collect_container_cpu.py &
python ui.py ETLTopologySys &
python ui.py IoTPredictionTopologySYS &
sleep 120
done
exit
kubectl exec nimbus -- /opt/apache-storm/bin/storm rebalance ETLTopologySys -n 6

for i in {1..77}
do
python collect_container_cpu.py &
python ui.py ETLTopologySys &
python ui.py IoTPredictionTopologySYS &
sleep 120
done


kubectl exec nimbus -- /opt/apache-storm/bin/storm kill ETLTopologySys

