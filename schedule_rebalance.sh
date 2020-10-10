rm /tmp/skopt_input_ETLTopologySys.txt

python collect_container_cpu.py &
sleep 120
for i in {1..10}
do
python ui.py ETL &
sleep 120
done

kubectl exec nimbus -- /opt/apache-storm/bin/storm rebalance ETLTopologySys -n 5

for i in {1..10}
do
python ui.py ETL &
sleep 120
done

kubectl exec nimbus -- /opt/apache-storm/bin/storm rebalance ETLTopologySys -n 6

for i in {1..10}
do
python ui.py ETL &
sleep 120
done

kubectl exec nimbus -- /opt/apache-storm/bin/storm kill ETLTopologySys

