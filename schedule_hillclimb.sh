rm /tmp/bo.log 
rm /tmp/bo_*
rm /tmp/kube-cpu.txt
rm /tmp/skopt_input*
rm /tmp/skopt_model*

bash script/redis-data.sh
python collect_container_cpu.py &
sleep 120
for i in {1..121}
do
python collect_container_cpu.py &
python ui.py ETLTopologySys &
python ui.py IoTPredictionTopologySYS &
python ui.py IoTPredictionTopologyTAXI &
python ui.py ETLTopologyTaxi &

sleep 45
python BO/hill_climbing.py >> /tmp/bo.log
sleep 75
done

kubectl exec nimbus -- /opt/apache-storm/bin/storm kill ETLTopologyTaxi
kubectl exec nimbus -- /opt/apache-storm/bin/storm kill ETLTopologySys
kubectl exec nimbus -- /opt/apache-storm/bin/storm kill IoTPredictionTopologySYS
kubectl exec nimbus -- /opt/apache-storm/bin/storm kill IoTPredictionTopologyTAXI

